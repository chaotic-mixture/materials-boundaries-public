# Migration to v0.29.0

This additive release introduces a separate concrete material registry and
reference-property catalogue, each with schema version **1.0.0**. The new
`catalog materials` and `catalog reference-properties` routes expose authored
four-language search and source-preserving text inspection. See the
[material reference guide](MATERIAL_REFERENCE_CATALOG.md).

The 41 existing mechanics claims, 16 observations, 12 computational predictions,
five synthetic temperature demonstrations, all old scientific schemas, and the
eight executable composite rules are unchanged. Existing source records are
preserved by ID; new bibliographic records append. Historical examples and
fixtures are not regenerated.

The package version advances to **0.29.0**; fresh evaluations/reports identify
that software version. Numerical behavior and pre-existing rendering contracts
remain unchanged. Strict saved-report replay continues to require the current
software/catalog snapshot, so a report produced under an older version may
need explicit regeneration from its original inputs. This does not invalidate
or rewrite the historical saved file.

The material catalogue does not add evaluation support, convert units, infer
missing conditions, or certify source correctness or reuse rights. Manufacturer
references and published measured summaries retain different evidence classes.
Reported mean, SD and sample count remain separate fields. Every new state must
resolve a source-backed numerical property. Subsequent valid identity/grade
additions are data contributions under the generic closed contract, not new
per-material Python families.

Existing JSON clients are unaffected unless they assumed the set of catalogue
commands or source-registry length was fixed. New records have distinct ID
prefixes and do not share old scientific namespaces. Source/condition details
must accompany any downstream use of a new reference value.
