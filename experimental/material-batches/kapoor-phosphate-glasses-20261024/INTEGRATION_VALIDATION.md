# Kapoor runtime validation

Implementation validation is in progress. This checkpoint does not claim
publication readiness or hosted CI success. The candidate's earlier Windows and
Linux results belong to the unchanged-runtime candidate tree.

The local data-only append passed strict catalog validation, exact predecessor
object/order comparison and unchanged second merge. `scripts/validate_catalogs.py`
then completed with exit 0 in 7.000 seconds. Six local wheels built offline in
8.016 seconds. These checks do not replace installed-package tests.

Fifteen focused native Windows query/overlap/stale-store checks passed with
zero failures, errors or skips in 118.520 seconds. The seven new preservation
tests passed with zero failures, errors or skips in 36.560 seconds. Complete
250-method targeted core and 552-method fresh installed validation remain
pending at this checkpoint; the final ledger must state exact terminal results,
retained failures and unexecuted scope before independent implementation review.

The first task-owned append helper failed an assertion before writing any
runtime data: it incorrectly expected source row order instead of the existing
production merge's sorted-ID append order. The helper was corrected to assert
the exact old prefix and exact candidate objects in that established order.
The production merger, source facts and scientific assertions were unchanged.

Main remains 1081. No push, main merge, deployment, DOI registration, raw-asset
upload or credential change has occurred. The isolated historical-replay
optimization is not part of this implementation.
