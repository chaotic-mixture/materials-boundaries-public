# One composite case, assumptions, evidence and replay

## Scope of v0.28.0

This offline workflow wraps the existing **eight** executable rules for a single
supplied case. It neither sweeps fractions nor adds a scientific model or data.
The unchanged instance 1.0.0 and evaluation 1.1.0 contracts remain authoritative.
The independent `composite-report.schema.json` envelope is version **1.0.0**.

The supported calculation uses two explicitly supplied volume fractions and
positive active K/G under supplied 3D, constituent-isotropic, effectively
isotropic, small-strain, linear-elastic, static, perfectly bonded conditions.
HS also needs paired non-strict K/G ordering. E and ν depend on this same case's
HS intervals only. Every base rule, including Reuss/Voigt bulk, conservatively
requires known positive active K **and** G in this implementation.

Unknown evidence remains unknown. A genuinely violated premise should not be
changed just to get an answer. Crossed phase ordering leaves four Reuss/Voigt
results available but no HS or derived E/ν. An absent zero-fraction phase still
needs its second record; tiny positive fractions remain active. Negative or
zero ν is not automatically invalid. These are conditional approximate bounds,
not measurements, certified outward-rounded enclosures, engineering allowables,
material recommendations or a joint attainable material design.

## Prepare, calculate, replay

```sh
# Unknowns are explicit; no material values or scientific assumptions are filled.
python -m materials_boundaries composite init --output case.json --lang en
# Alternatively, on a terminal; existing case.json is never overwritten.
python -m materials_boundaries composite init --interactive --output my-case.json --lang en
# Explicitly choose an original fictitious demonstration, not measured data.
python -m materials_boundaries composite init --original-demo --output demo.json --lang en
python -m materials_boundaries composite report demo.json --output demo-report --unit GPa --lang en
python -m materials_boundaries composite verify demo-report/bundle.json --json
```

Both terminal streams must be TTYs for interactive intake. Blank observations
mean unknown, not an approved scientific default. The wizard supports `/back`,
`/edit N` on review, `/cancel`, and an explicit `/save`. EOF and Ctrl-C cancel
without saving. Mass fractions are not converted; a missing volume fraction is
not complemented. No density or isotropy is inferred from a material name.
K/G units are Pa, kPa, MPa or GPa. A generic E/ν editor is deferred; import an
existing valid `literature_model` JSON with its complete raw-parameter and
condition-basis evidence through `composite report`. User-asserted measured
provenance does not establish independent specimen verification.

Input structure, applicability, numerical availability and scientific review
are separate report states. A fully unknown valid report is useful and can
replay successfully. Source/condition warnings precede numeric results. Eight
rows retain IDs, one-sided directions, blocked checks and available results.
The ledger shows observed/required values and supplied-evidence basis; the
trace retains normalization, unit conversion and E/ν corner dependencies.
Reports preserve bibliographic wording, exact locators, missing citations and
independent-review=false. They neither fetch papers nor upgrade source review.

## Files and API

The new empty output directory contains only `input.json`, `evaluation.json`,
`bundle.json`, `report.txt`, `report.html` and `manifest.json`. There is no CSV,
script, form, remote font/asset, telemetry or upload. HTML text is escaped;
bibliographic URLs are displayed as inert text. Source assets are not bundled.
The human view is a concise evidence report: repeated assumptions, limits and
gaps are consolidated without changing the complete per-rule JSON. Plain text
points to the machine files for the full audit record. HTML places complete raw
records in closed native details; essential warnings, source-specific locators
and review gaps remain visible without opening them. These native disclosure
controls do not use scripts.

All four languages, en/zh/ja/de, share identical machine JSON. Translation is
machine-assisted and has not received independent scientific/native review.
English scientific wording is also not independently reviewed.

```python
from materials_boundaries.composite import build_composite_report, validate_composite_report
from materials_boundaries.composite_render import render_composite_report
from materials_boundaries.composite_export import export_composite_report

bundle = build_composite_report(instance, output_unit="GPa")
validate_composite_report(bundle)
text = render_composite_report(bundle, lang="en", format="text")
html = render_composite_report(bundle, lang="en", format="html")
result = export_composite_report(instance, "new-report", output_unit="GPa", lang="en")
```

Public rendering verifies its bundle first. Export builds the case once and
renders its just-built core without re-evaluating for each presentation.
Catalog formula prose never becomes executable code. Unresolved input source
IDs remain unresolved; arithmetic is not blocked merely by an optional missing
citation. Original large input integers remain exact in Python and JSON; no
JavaScript Number conversion is used. Human modulus endpoints are approximate;
ν uses round-trip float text to avoid hiding strict-boundary rounding failures.

## Replay is not scientific certification

`verify` strictly parses the complete bundle, validates the embedded instance,
rebuilds it with the installed engine/catalog contract and compares canonical
contents. Altered IDs, checks, numbers, dependencies, policy, source locators,
gaps, review flags or stale versions fail closed. It never migrates or rewrites
an input. Hashes use sorted-key finite-number UTF-8 JSON and establish content
identity only. A consistently replaced entire bundle can replay; these hashes
do not authenticate its author or establish that citations/inputs are true.

The manifest hashes saved artifact bytes separately, excluding itself. Bundle
replay does **not** verify that report.html/report.txt remain unmodified. To
check exported bytes, compare every manifest entry's byte count and SHA-256
with the respective file. Neither check proves scientific validity:
**software replay only; does not verify the physical sample or prove a theorem**.

CLI codes:
- `report`: 0 for a valid report including unknown/violated applicability; 2 for
  malformed input, unsupported request or I/O failure; 3 after exporting a valid
  report containing at least one numerical-range error
- `verify`: 0 for exact replay, 2 for malformed input, 4 for altered/stale core
- `init`: 0 after save, 2 for invalid request/I/O/non-TTY, 130 for cancelled intake

## Filesystem guarantees and limitations

Only a new file or empty report destination is accepted. The parent directory
must already exist. Symlink components and `..` traversal are refused; IDs and
notes never become file paths. A directory-descriptor-based implementation is
required (currently POSIX platforms with `O_DIRECTORY`, `O_NOFOLLOW`, descriptor
relative operations and hard links). Unsupported platforms fail explicitly.

Report files are prepared in a private staging directory **inside** the selected
destination. Each completed file is exclusively published with a hard link;
existing files are never overwritten, and `manifest.json` is published last.
Ordinary parse/render failures write nothing. Ordinary staging/publish failures
attempt to remove only invocation-owned files and staging data; unrelated files added
concurrently are preserved. Single-case init similarly uses exclusive staging
and atomic new-file publication in its selected parent.

This is **not a crash-safe directory transaction**. Per-file atomic publication
and a manifest-last convention do not guarantee all-or-nothing visibility,
filesystem durability, or protection against a hostile concurrent writer or
abrupt process termination. Persistent I/O errors can also prevent cleanup. A crash or failed cleanup may leave partial files or a staging folder;
do not treat them as a completed report. Use a new empty destination, verify all
manifest hashes, and replay the bundle before relying on a saved export. No
existing output is silently reused. Local saving does not publish or share data.

## Evidence and interpretation boundaries

The historical HS 1963 original equations/proof remain uninspected; absent
locators remain null. Kochmann–Milton arXiv v1 cross-check locators are preserved.
Reuss has a standard positive-phase expression with contextual support, not an
invented inspected original equation. Meille–Garboczi isotropic identities are
text-checked with visual verification incomplete. The E/ν outer envelope is a
project derivation, not a theorem attributed to that paper. Original software
and curation licensing does not relicense third-party publications.

An effective measurement inside a calculated interval does not independently
validate the model; an apparent exceedance does not automatically refute a
theorem. This release has no measured-composite comparison API. Check quantity
and stress definitions, input phase values, units, fractions, all premises,
uncertainty and numerical policy before attempting such a comparison. Source
model E/ν, converted constituent K/G, chosen fractions and calculated effective
E/ν remain different records. Temperature, grade, cure state and measurement
uncertainty are not inferred.

The 30 original acceptance questions are represented by
`tests/test_composite_acceptance.py`, with further core, rendering, intake,
filesystem-failure and CLI tests. Static HTML structure and escaping tests are
not a substitute for browser, keyboard, accessibility or native-language review.
Browser keyboard/narrow-width QA has not been performed in this environment.
