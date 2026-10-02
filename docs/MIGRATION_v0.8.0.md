# v0.8.0 migration: four catalog-only crystal-stability templates

> Development-history note: this version was not a public release. The first
> public release is 0.16.0; its [release scope](MIGRATION_v0.16.0.md) and
> [license notices](../THIRD_PARTY_NOTICES.md) supersede historical distribution
> assumptions. Temperature demonstrations now use original synthetic data.


## Preserved contracts and release versions

- Append four claims to the original **22 unchanged claim records**, for **26 claims** total, including **eight stability predicates**
- Preserve all **20 source records** and both **observation records from one study** unchanged. Every new claim cites the existing Mouhat–Coudert source with its own equation locator; no source or observation is added
- Advance claims schema from **1.5.0 to 1.6.0**, identifier `urn:materials-boundaries:schema:claims:1.6.0`
- Advance package/engine to **0.8.0**. The original **eight composite evaluations** keep the same values, order, applicability conditions and evidence; their intended payload change is only `engine_version`
- Keep instance schema **1.0.0**, evaluation **1.1.0**, source **1.0.0**, observation **1.0.0**, locale **1.0.0** and comparison **1.0.0** unchanged
- Add no stiffness-input API, runtime eigensolver, specimen classifier, anisotropic calculator or stability plot. Catalog formulas remain display-only, never interpreted as code
- Preserve historical migration documents and historical checked-in visualization previews rather than relabeling them as current results

## New IDs and metadata

| Claim ID | Source name / Laue class | Independent constants | Source locator |
| --- | --- | --- | --- |
| `tetragonal_i_born_stability` | Tetragonal I, 4/mmm | C11, C12, C13, C33, C44, C66 | p. 224104-2, matrix Eq. (7), criteria Eq. (9) |
| `tetragonal_ii_born_stability` | Tetragonal II, 4/m | C11, C12, C13, C33, C44, C66, C16 | p. 224104-2, Eqs. (10)–(11) |
| `rhombohedral_i_born_stability` | Rhombohedral I / trigonal, −3m | C11, C12, C13, C33, C44, C14 | p. 224104-3, Eqs. (12)–(13) |
| `rhombohedral_ii_born_stability` | Rhombohedral II / trigonal, −3 | C11, C12, C13, C33, C44, C14, C15 | p. 224104-3, Eqs. (14)–(15) |

The reference is [Mouhat and Coudert, *Physical Review B* 90, 224104 (2014)](https://doi.org/10.1103/PhysRevB.90.224104), source ID `mouhat_coudert_2014_elastic_stability`. Table I fixes the source's I/II classes and independent-constant counts. “Trigonal” is an alias, not a fifth new claim or a separate source.

All four use the existing predicate shape: `claim_type: stability_criterion`, `direction: constraint`, `quantity: homogeneous_elastic_stability`, `quantity_dimension: logical_predicate`, `si_unit: null`, `bound_kind: null`, empty dependencies and `evaluation_support: catalog_only`. Null output unit means no physical output unit applies; it is not an unknown pressure unit or a measured dimensionless result. All stiffness parameters use pressure units; linear and quadratic inequality margins use Pa and Pa² respectively.

The schema adds explicit `elastic_symmetry` alternatives for `tetragonal_i`, `tetragonal_ii`, `rhombohedral_i` and `rhombohedral_ii`, each tied to its exact parameter set, full symbolic matrix and complete strict inequality set. Do not replace these fail-closed alternatives with a generic symmetry string or permissive free-form matrix. Existing templates keep their validation contract.

## Scientific migration checklist

All four require C11>|C12|, C33(C11+C12)−2C13²>0 and C44>0, plus:

- Tetragonal I: C66>0
- Tetragonal II: C66(C11−C12)−2C16²>0
- Rhombohedral I: C44(C11−C12)−2C14²>0
- Rhombohedral II: C44(C11−C12)−2(C14²+C15²)>0

Preserve these distinctions in data readers and documentation:

- **Tetragonal C66 is independent** in both classes; never impose the hexagonal relation. **Rhombohedral C66=(C11−C12)/2 is dependent** and is not a seventh/eighth independent parameter
- Keep every coupling sign in the full matrix: tetragonal II C26=−C16; rhombohedral C24=−C14 and C56=C14; rhombohedral II additionally C25=−C15 and C46=−C15
- Preserve the factor 2 and the **combined** C14²+C15². Bounding each coupling separately is insufficient. Rhombohedral determinant positivity alone is also insufficient because its coupling margin is squared in det(C)
- Use right-handed orthonormal Cartesian axes, z along the principal fourfold/threefold axis. In I, choose basal x along a Laue twofold axis; in II, keep a fixed basal orientation with allowed couplings. A new setting requires a full tensor transformation, and “rhombohedral” does not require a nonorthogonal primitive basis
- Voigt order is (xx,yy,zz,yz,xz,xy), with engineering strain (εxx,εyy,εzz,2εyz,2εxz,2εxy), no factor 2 on stress shear, and energy ½eᵀCe. Do not mix with unscaled tensor shear or Mandel matrices
- These conditions are jointly necessary and sufficient only for strict positive definiteness in the exact real symmetric template, about **stress-free equilibrium under homogeneous infinitesimal strain in the harmonic quadratic approximation**
- Equality fails strict stability. A marginal harmonic case requires the entire matrix to be **positive semidefinite with a zero mode**. Equality or a zero eigenvalue alongside negative eigenvalues is not merely marginal; nonnegative leading minors with zeros do not certify PSD
- Do not infer full phonon/dynamical stability, finite-load/prestressed stability, finite-strain strength, yield, fracture, higher-order marginal stability, 2D/plane-stress behavior or universal finite-temperature stability. Rounded/uncertain near-zero values remain unresolved without uncertainty treatment

The [stability guide](ELASTIC_STABILITY.md) records every matrix and exact invented boundary examples. The [16-case synthetic fixture](../examples/catalog/crystal-stability-synthetic.json) contains pass/fail/PSD/zero-plus-negative cases, not `validate`/`evaluate`/comparison inputs or material data. The [checked-in regression suite](../tests/test_crystal_stability_catalog.py) uses independent standard-library `Fraction` checks on 1,024 seeded matrices, distinct from the earlier separate 70-digit research checks. Those examples, symbolic factorizations, principal-minor/eigenvalue checks and rotation checks concern transcription and synthetic algebra; they are not material observations, independent proof review, peer review or specimen validation.

## Query and presentation migration

```sh
python -m materials_boundaries catalog claims --id tetragonal_i_born_stability --json
python -m materials_boundaries catalog claims --id rhombohedral_ii_born_stability --text --lang en
python -m materials_boundaries catalog claims --claim-type stability_criterion --direction constraint --text --lang zh
python -m materials_boundaries catalog claims --query "三方晶" --text --lang ja
python -m materials_boundaries catalog claims --query "trigonal" --text --lang de
```

There is no new query flag. The existing stability filter now selects eight records. The four new `catalog_name_<claim_id>` values are authored literal search aliases in en/zh/ja/de, bringing claim display-name aliases from twelve to sixteen per language; the two observation aliases remain separate. All-term casefold matching, AND-combined filters, original catalog order and canonical language-independent JSON are unchanged. Preserve source I/II labels, Laue classes, formulas, units and IDs. Scientific and native-language review of all authored translations remains pending.

## Comparison exports and downstream readers

The comparison bundle still includes only the original eight executable composite claims and their evidence. Its embedded claims-schema snapshot advances to **1.6.0**, while the comparison contract remains **1.0.0**. New predicates and observation summaries do not become inputs, evaluation records or overlays.

Regenerate old exports from their retained valid composite inputs with **engine 0.8.0**. Changing version labels alone is not a migration: fail-closed validation checks the actual engine and catalog payload. The same valid inputs retain their numeric curves. Read claims by stable ID and `evaluation_support`, not total catalog length or `claim_type` alone; a catalog match does not certify applicability.

Run schema/reference, exact-template, strict-boundary, four-language search/rendering and unchanged-evaluator regression checks after migration. Passing software checks does not establish independent scientific review. Existing APS copyright and absence of a verified general reuse license remain unchanged; no paper pages, PDF, figures, article prose or raw material data are bundled.

See [catalog reference](CATALOG.md), [stability conditions](ELASTIC_STABILITY.md), [source evidence](SOURCES.md), [model scope](MODEL.md), [language conventions](I18N.md) and [visualization](VISUALIZATION.md).
