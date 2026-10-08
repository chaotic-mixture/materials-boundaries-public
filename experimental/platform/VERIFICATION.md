# Integrated verification

2026-10-08, Python 3.12. A clean virtual environment installed all four packages from source with ordinary dependency resolution. Installed API and CLI smoke checks ran outside the source directory. pip check reported no broken requirements. The lock records the resolved runtime and QA dependencies; it does not include private local package paths. Optional mp-api/pymatgen dependencies were not installed.

- Federation: 19 tests passed.
- Query API: 21 tests passed.
- Lifecycle: 25 tests passed.
- Independent API/lifecycle plus end-to-end integration: 18 tests passed.
- Total: 83 tests passed.
- Golden demo: exact raw/typed/binding/staging/review/release linkage and zero admission checked; repeated independent runs produced byte-identical release archives.
- Installed CLI: materials-platform and materials-lifecycle passed outside source.
- Installed API: health, synthetic MP demo and disabled MP live path passed outside source.

Lifecycle independent review accepted the disclosed bounded, local envelope-only implementation, including its installed-wheel tests. This is not independent scientific approval. Integration tests were performed by the integration implementer; separate integration review is still appropriate before publication.

NOMAD bounded live search was independently verified in the preceding query-service review (1 returned entry, 73 matching entries, unique-material count unknown). This integrated run was offline/fixture-only. Browser rendering/mobile/download verification remains blocked; no browser pass is claimed. No GitHub publishing, deployment, schedule, workflow activation, credential or DOI operation occurred.

Only experimental/platform is staged. The baseline source tree is exactly 753705d22be9f37b6a7deeae734ddd806fe3fb00. The local baseline commit is a reconstruction of those verified bytes, not the upstream commit. Existing production source, version, fixtures and CI files are untouched.

## Distribution license correction

All four wheels were rebuilt after explicit LICENSE and THIRD_PARTY_NOTICES.md packaging was added. ZIP inspection verified exact copies of the existing MIT text and attribution notices in each wheel, with both files listed in distribution metadata. The query-service wheel retains its minimized NOMAD fixture and the notice naming its entry, source URL, declared CC BY 4.0 license, AFLOW origin and projection changes. Runtime code and fixture bytes were unchanged. Reinstalled rebuilt wheels passed the same 83 tests, dependency check, and outside-source CLI/API smoke checks.
