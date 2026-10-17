# NBS ten-reference local increment

This manifest integrates the three frozen packets at commit
`ba389d33c1fe53e16539dd7fc185c3bd0f444757` into the exact
`742890fb780142ad82e0b3a012498362c494d1ab` core baseline. The order is metals A,
metals B, then inorganic. It uses the existing offline integration command.

Ten new identities, ten states and ten crystallographic-density properties are
added: seven metal and three inorganic. No grade or source is added. The entire
source registry remains byte-identical, and the existing NBS source is reused.
Removal of only these ten additions restores all three baseline catalog bytes.

The actual command was run twice against the same immutable output. The first
created the package; the second returned unchanged with identical bytes and
modification time. The command's retained report distinguishes local growth of
ten from the released-main increment of zero. `review.json` describes the local
integration decision and its precise validation scope; it is not a human
scientific signature.

Source-specific page/value checks and the established limited NBS reuse findings
are reused from the frozen packets. No new manual approval or rights gate is
introduced. The manifest's only pending gate is deferred publication. Scientific
review and raw-reanalysis flags remain false; properties remain catalog-only,
non-universal and non-allowable. No source assets are bundled.

See [the ten values, counts and reproduction instructions](../../../docs/MATERIAL_GROWTH_NBS_NEXT_20261016.md).
Actual focused test outcomes are retained in the parent handoff rather than
invented by this manifest. No login, push, main merge, DOI registration or public
deployment occurs in this increment.
