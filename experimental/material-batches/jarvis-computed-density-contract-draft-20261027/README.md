# Isolated computed-structure-density contract draft

This is an **unapplied implementation draft**, prepared while the Sanchez
full-root regression keeps the live runtime, schema and tests frozen.
It admits no materials. The source/contract proposal and candidate-fact reviews
do not approve this implementation.

[implementation.patch](implementation.patch) adds one finite method enum and
its runtime constraints: computational evidence, calculation basis, mass density
and crystallographic basis. The existing measured-input-derived, empirical and
handbook constraints remain. No ID exception, density recomputation or new
material record is included. The public schema is generated from the draft.

The external stage is pinned in [draft-manifest.json](draft-manifest.json), with
the original and draft file hashes. Live runtime baseline hashes were checked
again after testing and still match. The stage contains copied local data, not
a new checkout or release.

[Validation](VALIDATION.json): ten focused draft tests and 29 existing material
reference contract tests passed, with no failures or skips in the final runs.
The two initial synthetic-fixture errors are retained separately. The unchanged
1180-identity working graph also passed draft validation; its pending admission
status is unaffected.

Remaining work includes independent implementation review, four-language labels
and rendering, historical recovery, integration, full regression and installation
checks. This patch must not be applied over the running Sanchez snapshot.
After that stage closes, recheck all baseline hashes before considering it.

```powershell
python -B test_isolated_contract.py --stage PATH_TO_ISOLATED_DRAFT -v
```
