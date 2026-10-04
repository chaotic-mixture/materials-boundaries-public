# v0.28.1: bounded native Windows composite saving

This compatibility release adds local Windows NTFS saving for `composite init`
and `composite report`; replay uses the same existing bundle contract. There are
no new scientific models, catalog records, evaluation rules or assumptions.
Instance 1.0.0, evaluation 1.1.0 and composite-report 1.0.0 remain unchanged.

Use the existing workflow in an ordinary local NTFS directory. The parent must
already exist, and the chosen output must be a new file or an empty/new report
directory. Existing content is never overwritten. The Windows backend rejects
all reparse-point components (including junctions and cloud placeholders),
network/device paths, ambiguous Windows names and unsupported filesystems.
Unicode and long paths are supported within Windows/filesystem limits without
changing machine settings. See the complete [filesystem contract](COMPOSITE_WORKFLOW.md#filesystem-guarantees-and-limitations).

POSIX retains its descriptor-relative safeguards. Both paths publish completed
files exclusively with hard links and place the manifest last. Failure cleanup
checks ownership and can leave residual data if identity acquisition or I/O
fails. Neither path is a crash-safe directory transaction, durability promise or
hostile concurrent-writer guarantee. Windows ACL behavior depends on the parent
and Python version; choose an appropriately restricted parent directory.

Software version labels change to 0.28.1. Replay deliberately rejects bundles
built with a different engine version; retain the old environment to replay an
old bundle, or explicitly regenerate a new report from its original input. The
input is not silently migrated, and old saved reports are never overwritten.
Canonical scientific/evidence contents and rendered semantics are otherwise
unchanged. A successful replay remains software reproduction only, not physical
sample verification or theorem certification.

Native Windows CI covers Python 3.10 and 3.13, Unicode/long paths, blank/demo
intake, four-language reports, bundle replay, collisions, rollback ownership,
reparse rejection, handle release and an isolated dependency-free wheel. The
Windows symlink test may skip if the runner lacks the required privilege;
junction rejection is a mandatory independent test. POSIX-specific fault tests
remain active on Linux, with separate Windows-backend failure tests. Pure branch
mocks and Linux tests are not native Windows verification: the exact candidate's
Windows CI must pass before that platform result is claimed.
