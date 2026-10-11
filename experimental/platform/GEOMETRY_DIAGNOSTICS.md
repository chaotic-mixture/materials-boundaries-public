# Private original-structure diagnostics

`query-service/geometry_diagnostics.py` is a Python 3.11+ standard-library,
checkout-only CLI. It is outside the `materials_query` package and is not a
wheel-installed entry point. It performs bounded local consistency calculations
for one or two exact NOMAD original structures. It has no network, scheduler,
installation, admission or registry operation.

All results remain **held**, including successful diagnostics. A successful exit
does not approve scientific interpretation, rights, reviewer identity or a
formal release. Existing catalog counts and historical review artifacts are
unchanged. Do not copy old `accepted`, confidence or check fields into a new
review as evidence. Do not commit input geometry, source HTML, third-party mass
tables or private reports to the repository.

## Inputs and independent byte pins

Supply three private JSON files, each no larger than 1,000,000 bytes, and each
with a separately provided exact file SHA-256. JSON duplicate keys, nonfinite
values and excessive numeric tokens fail closed. Files must be bounded regular
files. The loader reports fixed error codes without echoing paths or content.

The archive file is the original response to an exact-ID
`POST /entries/archive/query` projection. Its `data` contains exactly the caller's
one or two requested IDs, and `pagination.total` equals that count with no next
cursor. Each row has an outer `entry_id` and an `archive` containing:

- `metadata.nomad_commit`, matching the unit contract. If metadata also contains
  `entry_id`, it must match the outer ID.
- `results.material.material_id` and `chemical_formula_hill`. If `elements` is
  present, it must be unique valid symbols matching the source formula.
- `results.properties.structures.structure_original`: `dimension_types`,
  `lattice_vectors`, `cartesian_site_positions`, `species_at_sites`, `species`,
  `cell_volume`, `atomic_density`, and `mass_density`.

`species` contains objects with exactly `name`, `chemical_symbols` and
`concentration`. This first version supports unambiguous full occupancy of one
element per species, with concentration 1. Mixtures, partial occupancy, extra
mass/isotope fields, missing mappings and unused species definitions are held.
No disordered or isotope-specific interpretation is invented.

`n_sites`, when returned, must match the positions count. NOMAD's fixed source
defines it as a derived count; when it is absent, `site_count` is derived from
positions and checked against the species-label array. It is not described as
an independent measurement. The projection must use the selected
`structure_original`, not an idealized or companion structure. Capture-time
identity/revision/mainfile/density comparison against earlier evidence remains
a separate source-fidelity review; this tool does not accept an unrelated
historical row merely because its formula matches.

The caller-supplied mass file has exactly this shape (placeholders are not data):

```json
{
  "schema": "geometry-masses/1",
  "source": {
    "url": "https://official.example/immutable-source",
    "version": "SOURCE_VERSION",
    "sha256": "SOURCE_BYTES_SHA256"
  },
  "convention": "standard_atomic_weights",
  "masses_u": {"ELEMENT_SYMBOL": 1.0},
  "atomic_mass_constant_kg": {
    "value": 1.0,
    "source": {
      "url": "https://official.example/constant-source",
      "version": "CONSTANT_VERSION",
      "sha256": "CONSTANT_SOURCE_BYTES_SHA256"
    }
  }
}
```

Replace the example masses, constant and hashes with inspected, pinned data.
The module contains no real mass table or conversion constant. Source references
require a URL, a bounded version identifier and a lowercase 64-digit SHA-256.
The reference identifies supplied evidence; the tool does not authenticate the
source or inspect it over the network. `synthetic_test_only` is also supported
as an explicitly labeled convention for the original synthetic tests.

The unit file has exactly this shape:

```json
{
  "schema": "nomad-geometry-units/1",
  "source": {
    "url": "https://official.example/immutable-unit-source",
    "version": "SOURCE_VERSION",
    "sha256": "UNIT_SOURCE_OR_REVIEW_PACKET_SHA256"
  },
  "nomad_commit": "RECORDED_HEX_PROCESSING_COMMIT",
  "units": {
    "lattice_vectors": "m",
    "cartesian_site_positions": "m",
    "cell_volume": "m^3",
    "atomic_density": "1/m^3",
    "mass_density": "kg/m^3"
  }
}
```

No implicit angstrom conversion or unit guessing occurs. The caller must bind
the source definition and serving-contract evidence to the archive fields and
processing revision. Matching a supplied hash does not verify the truth of the
unit claim. A density calculated with standard atomic weights is a consistency
diagnostic under that convention, not isotope-resolved experimental density.

## Predeclared numerical checks

The defaults were chosen before inspecting the selected private geometries:

| Check | Rule |
| --- | --- |
| Periodicity | Exactly three integer periodic directions `[1, 1, 1]` |
| Cell and positions | Finite 3-by-3 row lattice and 1–256 Cartesian sites |
| Composition | Reduced integer element counts equal reduced source formula |
| Cell volume | `abs(det(cell))`; relative error at most `1e-8` |
| Atomic density | `N / computed_volume`; relative error at most `1e-8` |
| Mass density | `sum(site masses in kg) / computed_volume`; relative error at most `0.002` |
| Periodic duplicates | Minimum periodic separation strictly greater than `1e-13 m` |

Every relative error uses the positive, finite **source value** as denominator.
Source volume, atomic density and mass density are independently compared with
the calculated values; the tool never compares a new value with itself. The
volume and atomic-density defaults check numerical cell consistency, not
measurement uncertainty. A caller may tighten the three relative tolerances
through `diagnose`; it cannot loosen them. The CLI uses the fixed defaults.

Cells are scaled by their largest absolute component for inversion. The
normalized determinant must exceed `1e-12` in magnitude and the Frobenius
condition estimate `||A||_F ||A^-1||_F` must not exceed `1e6`. Scaled Cartesian
coordinate magnitudes must not exceed `1e6`. Unstable, underflowing, overflowing
or excessively expensive inputs are held, not repaired or truncated.

## Complete bounded periodic search

Lattice vectors are rows of `A`. For each displacement `r`, set `d = r A^-1`.
For an existing valid global distance upper bound `R`, any image that can improve
it obeys

```text
|(d + n)[i]| <= R * ||column_i(A^-1)||
```

The tool exhaustively enumerates the integer box defined by those three bounds.
Bounds are padded outward by a condition-scaled multiple of floating-point
epsilon and `nextafter`. Component rounding only supplies a trial upper bound;
it is never treated as the closest-image result. A fixed 27-image neighborhood
is not used. Cubic provider symmetry does not imply orthogonal supplied vectors.

Nonzero self-images are included; only the zero self-translation is excluded.
The same self-image lattice need only be searched once. Distinct site pairs are
then considered. A previous global minimum can tighten each subsequent box:
images outside it cannot improve the requested global result. Empty improving
boxes can be skipped. All reserved box points, including excluded zero self
translations, count against at most 2,000,000 evaluations per record. A box
exceeding the remaining budget is rejected before enumeration. This is a
bounded double-precision algorithm with explicit conditioning limits, not an
exact-arithmetic theorem about arbitrarily ill-conditioned cells.

## Run from any working directory

Use absolute paths to the checkout script and the private inputs. IDs beginning
with `-` use the equals form:

```powershell
python -B C:/CHECKOUT/experimental/platform/query-service/geometry_diagnostics.py `
  --archive C:/PRIVATE/response.json --archive-sha256 EXACT_ARCHIVE_SHA256 `
  --masses C:/PRIVATE/mass-table.json --masses-sha256 EXACT_MASS_FILE_SHA256 `
  --units C:/PRIVATE/unit-contract.json --units-sha256 EXACT_UNIT_FILE_SHA256 `
  --entry-id=EXACT_SELECTED_ID_1 --entry-id=EXACT_SELECTED_ID_2
```

Standard output is a deterministic JSON report containing identities, hashes,
scalar diagnostics, check outcomes, bounded-work counts and held state. It does
not contain cell/position/species arrays, original raw fields, source URLs or
private paths. Save this report and the exact command, Python version, exit
status and stderr in the private evidence workspace. The report binds both this
algorithm source and the reused composition-contract source by SHA-256.

Exit 0 means the configured consistency checks passed, while still held.
Exit 1 means a calculated consistency check failed. Exit 2 means malformed,
unbound, unsupported, unstable or over-budget input. No outcome emits a v2
accepted review or grants publication/admission authority.

The Python API is:

```python
diagnose(
    archive_bytes, mass_table_bytes, unit_contract_bytes,
    expected_archive_sha256=archive_pin,
    expected_mass_table_sha256=mass_pin,
    expected_unit_contract_sha256=unit_pin,
    expected_entry_ids=selected_ids,
)
```

`minimum_periodic_distance(cell_m, positions_m, max_evaluations=...)` is the
separately inspectable numeric helper. It returns only the global distance,
evaluation count, condition estimate and the self-image convention.

## Focused verification

From the checkout root:

```powershell
python -B -m unittest discover -s experimental/platform/query-service/catalog-tests -p test_geometry_diagnostics.py -v
```

The tests use original synthetic structures and explicitly synthetic masses,
not copied real geometry or a claim about elemental masses. They cover cubic
and triclinic cells; skew cases requiring translations beyond a fixed 27-image
box; self-images; duplicates; source denominator errors; occupancy and identity
failures; units and pins; numeric/JSON limits; work/conditioning limits; safe
output; and a CLI run from an unrelated directory. They are implementation
tests, not scientific review of a real material.
