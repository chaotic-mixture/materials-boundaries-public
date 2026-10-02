# Migration to v0.18.0

Version **0.18.0** adds exactly two catalog-only bulk elastic plane-wave
relations and two source records. This declaration does not claim a published
tag, release date or software DOI. The [v0.17.0 MoS2 addition](MIGRATION_v0.17.0.md)
and all earlier scientific contracts are preserved.

## Catalog and schema delta

- **36 mechanics claims**, up from 34, by appending
  `isotropic_bulk_plane_wave_speeds_and_ratio` and
  `christoffel_tensor_strong_ellipticity`
- **50 sources**, up from 48, by appending `chevrot_vanderhilst_2003` and
  `xiang_qi_wei_2018_arxiv_v2`; this is 49 bibliographic/source records and one
  original synthetic-demo provenance record
- Software/package/engine version **0.18.0**; claims schema **1.10.0 → 1.11.0**
- Sources schema **1.0.0**, observations schema **1.1.0**, evaluation schema
  **1.1.0** and the other scientific schemas remain unchanged
- **4 observations from 2 studies**, **6 computational predictions** and
  **5 synthetic temperature demos with 7 branches**, unchanged
- Exactly **8 executable composite rules**, with unchanged scientific behavior,
  applicability, rule order and evidence

Both new claims have `claim_type: model_relation`, `direction: relation`,
`bound_kind: null` and `evaluation_support: catalog_only`. They are neither
new bounds produced by the composite evaluator nor material measurements.
Existing claim and source record objects are preserved; an envelope-version
change is not a scientific rewrite of those records.

## New scientific distinctions for readers

The [bulk-wave guide](BULK_ELASTIC_WAVES.md) states the shared finite real 3D,
stress-free, homogeneous, local linear-elastic nondissipative model, Cartesian
symmetries and finite scalar density ρ>0. It separates:

1. **Finite positive K,G,ρ isotropy:** c_L²=(K+4G/3)/ρ and c_T²=G/ρ.
   The ratio over this material class is **(√(4/3),∞)**, with an unattained
   lower infimum and no finite class-wide upper bound; infinity is never a
   member. One fixed material has finite direction-independent speeds and a
   twofold transverse eigenspace
2. **All-direction strict strong ellipticity:**
   Q_ik=C_ijkl n_j n_l in Pa, Γ=Q/ρ in m² s⁻², and Q a=ρc²a.
   Strict positivity of all three c² for every unit n is equivalent to this
   rank-one criterion; real or merely nonnegative eigenvalues are insufficient
3. **Full symmetric-strain energy SPD:** this implies strong ellipticity but
   is not equivalent. The original K=−G/3, G>0 counterexample has Q=GI yet
   W(αI)=−3Gα²/2<0. Existing Born/full-energy criteria keep their stronger scope

Phase normal n and polarization a are distinct. Generic anisotropic modes need
not be exactly longitudinal/transverse, and no universal fastest-longitudinal
ordering is asserted. Phase speed is not an anisotropic ray/group-velocity
result. There is no automatic substitution of static/isothermal moduli,
thermoelastic conversion, incompressible endpoint, or material-specific input.

## Downstream compatibility

Readers that pin claims schema 1.10.0 or assume exactly 34 claims must update
their catalog-envelope handling. Keep stable-ID selection and catalog order;
never execute displayed formula strings or infer evaluator support from a
claim's presence. Search and canonical JSON remain language-independent;
curated en/zh/ja/de names and warnings are presentation metadata. No wave input,
new CLI evaluator, tensor inverse/eigensolver, wave plot, API for acoustic
moduli, numeric speed prediction or automatic comparison is introduced.

The two graphene and two monolayer MoS2 observations retain their distinct
uncertainty types and source conditions. **The MoS2 printed-q inconsistency and
unresolved actual fit constant remain visible; no correction or refit is made.**
There is no observation plot, material ranking or 2D-to-3D thickness conversion.
NIST cryogenic coefficients and their derived examples remain omitted; synthetic
temperature examples retain their deliberately invented coefficients/ranges.
Earlier claims, predictions, example artifacts and contributor workflows are
not removed or silently relabeled as newly verified.

Engine labels and identifiers derived from software version may change without
changing a numerical result. Do not relabel historical generated artifacts as
fresh evaluations; no new plot is required for this catalog-only release.

## Evidence and rights

- Chevrot–van der Hilst (2003), DOI
  [10.1046/j.1365-246X.2003.01865.x](https://doi.org/10.1046/j.1365-246X.2003.01865.x),
  printed p. 498 / PDF p. 2, Eqs. (1)–(4): general plane-wave equation and
  normalized Christoffel eigenproblem; the relevant equations were visually
  checked in an author/university-hosted journal-layout PDF
- Xiang–Qi–Wei, [arXiv:1708.04876v2](https://arxiv.org/abs/1708.04876v2),
  printed/PDF pp. 2, 4–5: rank-one criterion, tensor symmetries, isotropic
  stiffness and speed identities; those pages were visually checked. This is
  the January 2018 v2 preprint, not a verified journal version

The interval, index mapping, energy proof/counterexample, fixed-tensor bounds
and unit check are original project derivations. Source cautions include
explicit nonzero-vector quantifiers, symmetric-strain energy, and avoiding a
division by K+G/3 at the counterexample's degeneracy. Only the two source records
above are added; no third-source corroboration is promoted to catalog evidence.
No source PDF, figure, page image or full text is bundled. Copyright/reuse
qualifications remain source-specific, and arXiv distribution rights do not
become general reuse permission. MIT covers original project work only.
Independent scientific and native-language review remain unperformed.

## Verification checklist

From the repository root, with the complete development dependencies installed:

```sh
python scripts/validate_catalogs.py
python -m unittest discover -s tests -v
python -m materials_boundaries catalog claims --id isotropic_bulk_plane_wave_speeds_and_ratio --json
python -m materials_boundaries catalog claims --id christoffel_tensor_strong_ellipticity --text --lang en
python -m materials_boundaries catalog claims --id christoffel_tensor_strong_ellipticity --text --lang zh
python -m materials_boundaries catalog claims --id christoffel_tensor_strong_ellipticity --text --lang ja
python -m materials_boundaries catalog claims --id christoffel_tensor_strong_ellipticity --text --lang de
```

Check record/source preservation, references, strictness and normalization,
fixed-material versus class-wide statements, language-independent JSON,
four-language warnings, malformed scientific metadata rejection, installed-wheel
behavior and the unchanged exact eight-rule registry. This is a checklist, not
a statement that any particular check has passed. Software validation and
symbolic cross-checks do not certify real materials or replace scientific review.
