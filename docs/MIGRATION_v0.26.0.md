# Migration to v0.26.0

This bounded release appends two scalar viscoelastic catalog records and two
Hanyga bibliographic source records. Production totals become 38 claims and
55 sources. Observations remain 16 from five studies, predictions remain 12 in
two scientific families/three groups, and the five synthetic temperature demos
retain seven branches. Exactly eight composite rules remain executable.

Claims schema advances **1.11.0 → 1.12.0**. It adds two closed quantity families,
the narrowly scoped `dimensionless_response_product_bound`, and parameter-only
`time`/`s` and `inverse_time`/`s^-1`. Those parameter dimensions cannot be attached
to older families. `viscoelastic_contract` is closed and forbidden on other
families. Full validation resolves the product dependency to one admitted
scalar-duality family; a fresh paired record may use fresh IDs, with the same
reviewed scientific contract. Scientific formulas, units, assumptions, endpoints,
proof roles and parameter meanings cannot be replaced by arbitrary strings.

The comparison schema's embedded claims snapshot and exact reference advance
with the standalone claims schema. Its own schema version stays unchanged.
Old comparison outputs containing the older catalog envelope must be regenerated
for validation against the new embedded catalog schema. Numerical outputs and
rendering contracts do not otherwise change. Source schema stays 1.0.0; no
observation, prediction, temperature or evaluator schema changes.

The software-version label changes to 0.26.0. All 36 earlier claim objects, all
53 earlier source objects, all other production catalogs, old locale values,
fixtures and generated examples remain unchanged. Current-schema assertions and
the exhaustive no-dependency-family selector advance explicitly; narrow tested
compatibility reversals preserve the older byte-level lineage checks.

See [the scientific guide](SCALAR_VISCOELASTICITY.md) for the all-conjunctive
scope, original finite-interval absolute-continuity/jump proof, normalized duality,
original conditional product bound, analytic Maxwell/SLS checks, exact source
versions, locators and rights limitations. No numerical viscoelastic evaluator,
fit, observational data, universal material-strength bound, passivity equivalence,
creep strength or rupture predictor is added.
