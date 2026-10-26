# Offline formal-catalog overlap diagnostics

This standard-library-only command audits the pinned **1199 formal entries** and
compares explicitly supplied local clues. It addresses a gap in
`nomad_review_boundary`: that index checks the 1175 legacy bytes and count but
indexes only the computed composition groups. The existing catalog text search
does not search all reported composition text. The new command reuses the formal
catalog's admission pins, the existing composition parser, canonical hashes,
strict JSON decoding, canonical taxon keys and the reviewed wood crosswalk pin.
It creates no material, source adapter, candidate packet, approval request or
admission. It never fetches a URL or writes an input/catalog/cache file.

## Run locally

From this directory, using Python 3.11+:

```sh
python -B formal_overlap_audit.py > /absolute/local-evidence/field-coverage.json
python -B formal_overlap_audit.py --probes /absolute/local-evidence/probes.json \
  > /absolute/local-evidence/overlap-diagnostics.json
python -B -m unittest -v test_formal_overlap_audit
```

The output goes to stdout; choose a separate output path, never an input or
catalog file. Python bytecode writing is disabled before local imports. CLI
input is capped at 65,536 bytes and 20 probes; output is capped at 12,000,000
bytes, including its final newline. A failure exits 2 with a generic error and
no partial report. Duplicate JSON keys, unknown probe fields and nonfinite
numbers are refused. No package installation, credentials or network is needed.
This command reads the repository's explicitly pinned formal package resources;
a changed release fails closed rather than silently extending coverage.

Example diagnostic input (these are user-supplied clues, not provider records):

```json
{
  "schema": "formal-overlap-probes/1",
  "probes": [
    {"probe_id": "al2o3_formula_only", "formula": "Al2O3"},
    {"probe_id": "alumina_manual_hint", "formula": "Al2O3", "terms": ["alumina"]}
  ]
}
```

`alumina` is an explicit human search hint; it is not a synonym inferred from the
retained Alexandria fragment. The earlier fragment supplies the Al2O3 formula
only for this comparison and remains a reserialized, incomplete tool artifact.
It is not refreshed, imported, or promoted by this command.

## Field coverage and scope

Every formal ID appears once in `rows`, with its frozen identity-content digest,
source file label and JSON pointer. The mutually exclusive
`primary_comparability_partition` is:

| Primary comparison channel | Entries | Interpretation |
| --- | ---: | --- |
| Structured integer composition | 24 | Reviewed computed composition and NOMAD references; phase/site-order and global equivalence remain unresolved. |
| Scoped canonical taxon identity | 1000 | Accepted WFO ID, tissue scope and historical backbone; no formula is inferred. |
| Advisory taxon crosswalk | 6 | Five conservative wood/culm exclusions and one cork-versus-wood non-merge rule; these do not repair or replace legacy taxonomy. |
| Source-qualified text only | 169 | Names, aliases, source/processing scope and sometimes grades or composition prose; no typed composition or canonical taxon key. |

These four classes sum to 1199. Separate field dimensions **overlap**: 166 legacy
entries have source-supported composition/purity prose, 31 have linked grades,
and 37 are composites. Do not add those dimensions to estimate coverage. All
1175 legacy identities lack a structured stoichiometric-composition field.
The prose is useful evidence for manual comparison, not a trustworthy machine
formula. Purity ranges, starting powders, additives, constituent ratios, supplier
grades, specimen state and final retained phases are different claims.

The five Tarasov PNA-BPF formulations contribute five qualified-text entries,
each with one DDS-cured state and no grade. Their nominal HCP:BPF:ECH feed
labels remain literal source prose, with inconsistent reagent entries and
unknown final composition. They do not become structured compositions or pure
molecular species, and a shared feed-label clue remains only a possible overlap.

The six Kapoor glasses add six source-qualified text entries and six linked
as-prepared states, no grades, and no structured stoichiometric composition.
Analyzed oxide mol% is not a nominal recipe or a pure-species assertion.

The two Tian composites add two source-qualified text entries, two as-extruded
states and no grades or structured compositions. Their nano-Ti loadings are
nominal, not analyzed final compositions; the unreinforced comparator is excluded.
They add no Al2O3 cue to the bounded check below.

`composition_prose_paths`, linked grade/state counts, canonical taxon fields,
crosswalk dispositions and source pointers identify exactly which formal records
have each channel. Each matched clue carries its path and qualifying identity,
state and composition notes. Evidence URLs, negative notes, identity-scope prose,
and unrelated source-scope comparisons are not positive search fields.

## Three diagnostic outcomes

- `confirmed_overlap`: the caller provides an exact formal ID **and** its
  frozen `identity_sha256`, with no conflicting supported probe facts. The
  `proof_scope` is `frozen_formal_record_reference`: this proves reuse of a
  catalog identity record, not that an external crystal/specimen is physically
  identical. Copying a public ID/hash does not authenticate the external claim.
- `possible_overlap`: a structured composition, provider/taxon reference,
  crosswalk or literal textual clue matches. This includes identical formulas
  for different structures, shared ingredients, grades from different suppliers,
  and same taxon with different tissue/backbone. Conflicts remain explicit;
  they are never resolved by choosing a convenient interpretation.
- `unable_to_compare`: no supported overlap evidence was found. This includes
  different structured values, missing fields and text that does not match the
  literal probe. It is **never** a new-material verdict or admission eligibility.

All results set `physical_equivalence` to `unasserted`, `new_material_count` to
null and `admitted_delta` to zero. The tool is not a complete chemical ontology,
structure matcher, taxonomic reconciliation engine or novelty detector.

The formula parser handles only simple integer stoichiometry and provides an
advisory reduced-composition key. Formula matches in legacy text are literal,
case-sensitive and word-bounded: `Co` does not match `CO`, and `Al2O3` does not
match `Al2O30`. Unsupported formulas are refused; compound names, product aliases
and grade strings are never parsed into structured composition. Caller-supplied
`terms` use case-insensitive literal matching and are clearly marked as such.
No stemming, synonym expansion or fuzzy matching is performed.

## Optional explicit reference clues

Each probe requires a unique `probe_id` and at least one comparison field.
Supported optional fields, with no extra keys, are:

- `formula`: a supported simple integer formula.
- `terms`: one to eight distinct literal phrases, each 2–80 characters.
- `formal_reference`: `{ "id": "...", "identity_sha256": "..." }`, copied
  from an audit row only for exact local record-reference diagnostics.
- `provider_reference`: `{ "provider": "nomad", "material_id": "..." }`
  and/or `entry_id`. Matching either is a source-reference relation, not a
  physical-equivalence or composition-bucket approval. Existing related-group
  links in the frozen formal review remain advisory and never create more
  formal entries. Material/entry pairs not present together are flagged.
- `taxon_reference`: `{ "accepted_taxon_id": "wfo-0000000000",
  "tissue_scope": "...", "backbone_sha256": "..." }`. A shared taxon remains
  a possible relation; tissue and backbone disagreement is retained.

Reference assertions are diagnostic input only. They do not register a provider
or grant trust. A differing formal digest cannot yield a confirmed match.
All probes and output rows are deterministically ordered; canonical input hashes
bind each probe without echoing arbitrary search terms into a new source record.

## The bounded Al2O3 check

A formula-only probe finds thirteen possible legacy relations and no confirmed
overlap: A16SG-derived alumina, an AlN/Y2O3/Al2O3 starting mixture, and a
Si3N4/Al2O3/Y2O3 starting mixture, four Bruns NBS2 glass formulations, and six
Kapoor calcium phosphate/aluminophosphate glasses.
The Bruns nominal oxide recipes and separate ICP-OES assays remain qualified
composition prose, not inferred pure stoichiometric compounds. No assay correction,
recipe normalization or final purity is inferred. Each recipe has one linked
furnace-cooled state; quenched states are excluded, and thermal history does not
create extra identities. Their actual composition text and qualification notes
remain attached. Kapoor uses analyzed ICP-OES mol% without normalization; its
three reported zero Al2O3 entries also match the literal text probe and do not
prove nonzero alumina content. Its annealed/reannealed as-prepared states
remain separate from excluded compressed states. None is treated as an ideal
pure Al2O3 crystal. The other
1179 entries are `unable_to_compare` for this probe; that count is a diagnostic
coverage gap, not a count of novel materials or an assertion that overlap is
impossible. No new Alexandria network read is performed.

The complete output inventories only formal 1175 + 24 entries. The 62 excluded
examples, the older seven examples, related provider groups and calculation
counts are never added to the formal total. This local diagnosis changes no
scientific, licensing or admission decision and generates no approval workflow.

These are the appended experimental catalog boundaries at data commit
`bdb1e081d5860c4c69fbcd4ee41e01450dc7a921`.
Previously retained 1081-entry, 1103-entry, 1107-entry, 1108-entry, 1114-entry, 1116-entry, 1124-entry, 1127-entry, 1133-entry, 1136-entry, 1148-entry, 1168-entry, 1172-entry, 1177-entry, 1183-entry, 1185-entry, 1188-entry and 1192-entry diagnostic reports
remain historical evidence and are not rewritten.
