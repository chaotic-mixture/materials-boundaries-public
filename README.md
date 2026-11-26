# Materials Boundaries

An open, source-qualified materials database and executable mechanics toolkit. Explore material records with their conditions and sources, then run calculations whose assumptions and limits remain visible.

**Current software release: v0.38.0**

[Install and release notes](https://github.com/chaotic-mixture/materials-boundaries-public/releases/tag/v0.38.0) · [Database format](docs/DATABASE_FORMAT.md) · [Mechanics and knowledge base](docs/EXECUTABLE_MECHANICS.md) · [Contribute data](docs/DATABASE_CONTRIBUTING.en.md)

## Try the database

Python 3.10 or newer is required. Runtime use has no third-party dependencies. Install the project wheel:

```sh
python -m pip install "https://github.com/chaotic-mixture/materials-boundaries-public/releases/download/v0.38.0/materials_boundaries-0.38.0-py3-none-any.whl"
```

Query a source-qualified material record, inspect the polymer collection, or export and verify a snapshot:

```sh
materials-database query --query C11000 --quantity mass_density
materials-database summary --category polymer
materials-database export --query C11000 --quantity mass_density --output copper-snapshot
materials-database verify --snapshot copper-snapshot
```

A reported C11000 copper reference density is 8.9 g/cm³. Its source does not report the measurement temperature, specimen count, or numerical uncertainty. The database preserves those gaps instead of supplying defaults.

## Run a mechanics example

The first uniaxial tension scenario uses annealed Nickel 200, a reference Young's modulus of 205 GPa, and an explicitly accepted linear-elastic model:

```sh
materials-tension --strain .001 --assume-model
```

At an axial strain of 0.001 (0.1%), the result is 0.205 GPa. The output identifies the record, material state, source locator, boundary conditions, inputs, and rules used.

Three guided cases cover a normal calculation, a missing-modulus prompt, and reassessment after changing the lateral constraint. [Run the three tension cases](docs/EXECUTABLE_MECHANICS.md). The reference modulus comes from the [Special Metals Nickel 200 technical bulletin, Table 4](https://www.specialmetals.com/documents/technical-bulletins/nickel-200.pdf). Applying that dynamic elastic reference to a tension estimate requires explicit user acceptance and assumptions of no initial stress, no thermal strain, isotropy, and small-strain linear elasticity. Results do not predict yield, failure, or design allowables.

## Explore the material families

The database organizes source-qualified identities across polymers, metals, inorganics, composites, and natural materials. Use `materials-database summary --category polymer` and replace `polymer` with `metal`, `inorganic`, `composite`, or `natural` to inspect another family.

The collection includes experimental and computational records. A record count is not a count of independent experiments, and a material may have incomplete properties or conditions. See the [five material-family reading guides](docs/reading/README.md) and the [recycled polypropylene composite comparison](examples/recycled-pp/README.md).

## Language support

English is the default interface language. The CLI and getting-started guides also support Simplified Chinese, Japanese, and German. Select a language with `--lang en|zh|ja|de`.

- [English getting started](docs/GETTING_STARTED.en.md)
- [简体中文快速开始](docs/GETTING_STARTED.zh.md)
- [日本語のはじめに](docs/GETTING_STARTED.ja.md)
- [Deutsch: Erste Schritte](docs/GETTING_STARTED.de.md)

Canonical identifiers, JSON keys, units, and status codes remain stable across languages. Scientific explanations and translations are machine-assisted and have not received independent scientific or native-language review. See the [language contract](docs/I18N.md).

## Data quality and scientific scope

Records keep source wording, material state, test conditions, evidence locators, and unknowns distinct. Software validation checks structure and reproducibility. It does not establish scientific peer review, specimen applicability, engineering qualification, or reuse rights for third-party source material. The project code is [MIT licensed](LICENSE); data sources retain their respective rights. See [third-party notices](THIRD_PARTY_NOTICES.md).

## Project references

- [Download release v0.38.0](https://github.com/chaotic-mixture/materials-boundaries-public/releases/tag/v0.38.0)
- [Database schema and fields](docs/DATABASE_FORMAT.md)
- [Executable mechanics and knowledge base](docs/EXECUTABLE_MECHANICS.md)
- [Data contribution process](docs/DATABASE_CONTRIBUTING.en.md)
- [Release checks and validation](docs/DATABASE_CI.md)
