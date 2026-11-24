# Temperature examples

Run an empirical example from the repository root with `python -m materials_boundaries temperature evaluate examples/temperature/al6061-77k.json --json`. The nine alloy inputs cover in-range, overlap and out-of-range cases. See [NIST models](../../docs/NIST_TEMPERATURE_MODELS.md) for source tables and reuse status.

## Synthetic demonstrations

These inputs exercise artificial polynomial branches and boundary handling.

Inputs:

- `synthetic-linear-50k.json`: one branch, value 15
- `synthetic-linear-outside-5k.json`: outside the artificial interval
- `synthetic-overlap-50k.json`: inclusive shared endpoint, values 25 and 32.5
- `synthetic-quadratic-75k.json`: nonmonotonic quadratic demonstration
- `synthetic-quartic-100k.json`: all five polynomial coefficients exercised
- `synthetic-interval-overlap-70k.json`: interval overlap, values 53.5 and 58.25
- `synthetic-interval-outside-10k.json`: outside both artificial intervals

Overlapping branches remain separate. The software does not select or average
one of their values. Decimal output digits reflect arithmetic, not measurement
precision. Source-data intervals and fit-error values are not applicable and are
stored as null, with explicit synthetic status.

`visualization/` compares the linear and shared-endpoint models.
`catalog-visualization/` includes the full current catalog, initially five models
with seven branches. Both include canonical JSON, CSV, and static HTML plus wide
and narrow SVGs in English, Chinese, Japanese and German. They work offline and
contain no scripts.

Rebuild every export from the repository root:

```sh
python examples/temperature/regenerate.py
```
