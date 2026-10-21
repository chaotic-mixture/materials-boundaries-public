# Availability of the original batch evidence

This note clarifies evidence references in the original
`zenodo-8089569-filaments-20261021` packet at commit
`5cc1418392696dc8115581ad693dabfc2695422e`. It does not revise that packet,
its hashes, its nineteen candidate decisions or its admission outcome.

`finite-identity-inventory.json` is a retained local review artifact. It was
**not published in this repository**. The `finite_inventory.path` field in
[packet-spec.json](packet-spec.json) and [prepared-packet.json](prepared-packet.json)
is a historical local artifact identifier, not a repository-relative download
URL. A request for that filename under this public batch directory therefore
does not retrieve the retained inventory.

The original inventory has SHA-256
`95f73069e9c3b5a1da46d6b14d61e0e4d726e327064a3c8f853f0676cef86fef`.
It records 1,536 selected local file paths representing 298 unique byte payloads,
with no recorded JSON parse errors. Its scope combines the pinned predecessor
catalog with retained candidate and recovery evidence across local checkouts.
The complete manifest includes local environment paths and matched records from
external-only evidence. It is not copied into the public repository.

The `external_evidence` reference to `novelty-admission-review.json` is also a
local evidence locator, not a public URL. The retained standalone review hash is
`459d8c537e6643d7b08eb54e05bca2bb976e7d98d701e7902bee8802bf98f093`.

The public packet includes the nineteen candidate decisions, their rationales,
classification limits and the summary of the finite review:

| Public file | JSON pointer |
| --- | --- |
| [packet-spec.json](packet-spec.json) | `/review/identity_review` |
| [prepared-packet.json](prepared-packet.json) | `/input/review/identity_review` and `/review/identity_review` |

These published decisions can be inspected directly. The complete local
1,536-file comparison cannot be independently reproduced from this repository
alone. The inventory hash identifies the retained bytes; it does not establish
public availability, independent scientific review or global material novelty.

Any later adjudication of previously deferred candidates must identify its own
evidence and decisions separately. Neither this note nor a later availability
summary replaces the original inventory or silently rewrites the original
packet. Original workbooks, manufacturer documents and local review assets
remain excluded from the repository.
