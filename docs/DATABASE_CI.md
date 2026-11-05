# Development and release checks

`database.yml` runs database and executable-mechanics tests, one current-material graph check, and export/verification on normal pushes and pull requests.

`public-release.yml` runs on main, release branches, v* tags, and main-targeted PRs. It checks current data, database behavior, the new mechanics models, existing mechanics engine, input validation and release metadata. It then builds and installs the wheel and exercises installed commands outside the checkout on Linux and Windows, Python 3.11 and 3.12.

`ci.yml` is now explicitly `legacy-full-history-replay`, triggered manually. It retains historical byte-pinned regression jobs; these are useful for historical compatibility investigations and do not silently become acceptance evidence for a new release.

Stable releases require the current release checks for the exact source commit and installable assets. Passing tests does not grant independent scientific review or source redistribution rights. Remote branch-protection settings are separate from these workflow files.
