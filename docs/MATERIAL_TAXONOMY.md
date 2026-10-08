# Five-class material taxonomy

Taxonomy policy **1.0.0** (`natural-biological-tissue-v1`) uses five primary
classes: `metal`, `inorganic`, `polymer`, `composite` and `natural`. This is a
catalogue classification policy, independent of the software version and the
material/reference envelope versions. It does not extend the eight-rule
calculator, establish scientific equivalence or create a new material identity.

## The natural boundary

`natural` covers source-qualified biological tissue and native biological
fibers, preserving the source-declared tissue or fiber identity. Wood, natural
cork tissue, bamboo culm, flax/hemp technical-fiber bundles, native silk and
wool are the admitted legacy examples. Their preparation still matters:
cleaning, degumming, conditioning, boiling or another reported treatment does
not alone turn a tissue/fiber identity into a purified polymer or an engineered
composite. The existing state and method evidence remains authoritative.

Biogenic feedstock is not enough to establish this class. Extracted kraft
lignin, formulated natural-rubber compounds, processed/isolated biopolymers and
unfilled polymer blends retain `polymer`; the lignin-filled PBS formulation
retains `composite`. Rocks and minerals remain `inorganic`, including the
existing Carrara marble and K1 quartz arenite. Natural geological origin is
not the biological-tissue boundary used here. The catalogue does not infer an
unrecorded processing history, purity, anatomy or constituent fraction from a
primary category.

## The reviewed migration

The baseline is software v0.34.0, commit
`7e37be919ee97f1275249dcf745f9f55e951986a`. Exactly these ten identity IDs move
to `natural`:

| Identity ID | Previous class | Retained source identity |
| --- | --- | --- |
| `mat_usda_sugar_maple` | `composite` | Sugar maple wood |
| `mat_usda_northern_red_oak` | `composite` | Northern red oak wood |
| `mat_usda_sitka_spruce` | `composite` | Sitka spruce wood |
| `mat_stochioiu2024_flax_technical_fiber` | `composite` | Romanian flax technical-fiber bundles |
| `mat_stochioiu2024_hemp_technical_fiber` | `composite` | Romanian hemp technical-fiber bundles |
| `mat_cheng2019_bombyx_mori_silk_strain932` | `polymer` | Strain 932 native silk, control diet |
| `mat_arbelaiz2024_latxa_wool` | `polymer` | Selected soap-cleaned Latxa wool |
| `mat_prasetia2024_qsuber_reproduction_cork` | `composite` | Quercus suber reproduction cork |
| `mat_drury2023_moso_bamboo_culm` | `composite` | Phyllostachys edulis culm |
| `mat_drury2023_guadua_bamboo_culm` | `composite` | Guadua angustifolia culm |

The 57 legacy identities therefore have class counts **metal 14, inorganic 16,
polymer 14, composite 3, natural 10**. The migration creates no identities,
grades, states, sources or numerical properties; the original 20 grades and
57 state/property pairs remain.

The packaged [exact migration ledger](../materials_boundaries/data/taxonomy_migration_v1.json)
records the before/after value of every changed field, baseline commit,
policy version, catalogue hashes and complete retained-object hashes. The
34 changed leaf fields are:

- Ten identity `category` values
- Ten identity `identity_scope` values, replacing only the old classification
  wording
- Seven state `source_scope` values carrying the same classification sentence
- Seven property `scope_note` values carrying the same classification sentence

The USDA state/property scopes do not duplicate the old category claim and
need no prose edit. The other seven records retain matching identity/state/
property scope text. These are the complete classification-phrase replacements:

| Before | After |
| --- | --- |
| Natural biological-composite classification | Natural biological-tissue classification |
| Composite is a broad curation mapping to natural lignocellulosic structure | Natural is a broad curation mapping to biological tissue with natural lignocellulosic structure |
| Polymer is a broad natural-protein-fiber mapping | Natural is a broad native-protein-fiber mapping |
| Polymer is a broad natural keratin/protein-fiber classification | Natural is a broad native keratin/protein-fiber classification |
| Composite is a broad mapping for hierarchical natural tissue | Natural is a broad mapping for hierarchical biological tissue |
| Composite is a broad mapping for hierarchical natural lignocellulosic tissue | Natural is a broad mapping for hierarchical biological lignocellulosic tissue |

All surrounding prose is retained. Identifiers, object versions, names,
aliases, grades, state facts, processing/conditioning, numerical values,
original numeric/unit strings, statistics, uncertainty, sample counts,
methods, scientific scope, evidence, source locators, rights and verification
flags are unchanged. Historical release documentation, fixtures and examples
continue to describe their historical four-class snapshots. A current class
filter or rendered category for one of these ten records deliberately differs
from that snapshot; it must not be reported as byte-identical old output.

## Identity and deduplication

Legacy stable catalogue IDs remain in place. A category, display name, alias,
source row, grade or processing state is not by itself a new material identity.
This migration adds no WFO accession and no inferred taxon/tissue metadata.
Existing botanical names are preserved as source-supported labels without
silently asserting a new accepted-name resolution.

Future natural-material imports may use independently curated accepted-taxon
and source-declared tissue keys. A raw wood import requires a verified WFO
accepted identity and the source's actual tissue scope. A source describing a
wood collection without anatomical resolution remains **woody tissue,
anatomy unspecified**; do not invent heartwood, sapwood, stem position or a
whole-organism scope. The migration's finite identity inventory is a historical
audit, not a whitelist limiting later independently qualified materials.

A curated crosswalk is needed to equate a legacy catalogue identity with a new
canonical taxon/tissue key. A scientific-name string match alone does not
provide that crosswalk. Tissue distinctions must stay explicit, particularly
wood versus cork from the same accepted taxon. Neither new aliases nor
repeated source rows may inflate the independently resolved identity count.

## Replay and verification

The dependency-free `materials_boundaries.material_taxonomy` module exposes:

- `load_taxonomy_migration()` returns the exact pinned policy/ledger in a fresh
  object; a missing or edited resource fails closed
- `apply_taxonomy_migration(materials, properties)` returns independent migrated
  copies of the exact baseline snapshots, without writing files
- `apply_taxonomy_migration(materials, properties, reverse=True)` reconstructs
  the exact baseline snapshots from the exact migrated snapshots
- `verify_taxonomy_migration(materials, properties)` checks every complete
  retained identity, grade, state and property and the catalogue metadata while
  permitting independent suffix appends

Replay rejects already migrated, mixed, partial, altered or appended inputs;
it is deliberately an exact historical operation. The verification route
accepts independent append-only growth without weakening retained-object pins.
It checks new record IDs for uniqueness but **does not admit new scientific
records**. Ordinary schema, source, material-contract, rights and independent
transcription validation remain necessary. Neither operation runs
implicitly during ordinary catalogue reads, and no record is reclassified by
name matching.

Run the focused checks with:

```sh
python -m unittest discover -s tests -p test_material_taxonomy.py -v
```

Tests prove exact baseline-byte recovery, the complete 34-field difference,
unchanged nonclassification payloads, source-scope synchronization, deliberate
mineral/processed-polymer exclusions, absence of fabricated taxonomy metadata,
independent appendability and rejection of changed retained science or ledger
contents. These software checks are not fresh source inspection, scientific
peer review, raw-data reanalysis or legal clearance. Whole-tree historical
recovery, full validation, four-language views and installed-wheel tests remain
separate integration requirements.
