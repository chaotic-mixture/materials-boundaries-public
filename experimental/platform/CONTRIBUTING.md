# Contributing to the experimental platform

Keep changes within this directory; do not change frozen production data, identity counts or release metadata as a side effect. Run all four test suites and package installation checks. Keep adapter code in federation only; query-service consumes its local package dependency. Each package remains separately installable (install federation before query-service).

Use original synthetic fixtures for new tests. Describe fixture origin, license, source profile, exact fields and expected failures. Real provider excerpts need minimal scope, attribution and reuse review; do not include credentials, raw private assets or bulk downloads. Never infer experimental evidence, uncertainty, specimen state or canonical identity from absent fields. Unknown stays unknown.

Contributions enter staging with explicit provenance and pending/held status. A separate identified reviewer must inspect the exact content, rights, numeric semantics and source status before any real release decision. Local reviewer strings are not authenticated identity. A digest is content binding, not independent scientific validation. See lifecycle/CONTRIBUTING_DATA.md. Publishing, credentials, schedules and production admission require separate authorization and review.
