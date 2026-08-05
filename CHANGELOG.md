# Changelog

## 0.1.0 - 2026-08-05

### Features

- [2efdc40] Bootstrap new repositories from GitHub metadata
- [49157ab] Add current_python_version function and update minimum Python version handling
- [85c3e3b] Auto-insert and verify SPDX headers
- [d994605] Generate CHANGELOG.md with git-cliff
- [a0422df] Add release preparation script
- [a8292bc] Substitute SPDX and release metadata
- [ccaa380] Update package ecosystem from pip to uv
- [e483e23] Add check for unquoted YAML clock values and update SPDX files
- [0e3964a] Run pre-commit hooks before committing changes
- [de14a92] Update pre-commit hook command to use 'uv' prefix
- [71e61eb] Add run_hooks function to execute pre-commit hooks on release files
- [81de170] Enhance changelog generation and normalization process

### Bug Fixes

- [deb91e6] Correct syntax error in CI workflow configuration
- [18528c0] Update README.md
- [38f4142] Bootstrap repositories only while placeholders remain
- [572d31e] Restore placeholder package and prevent self-bootstrap
- [a3bd78d] Run one tox Python env per matrix job
- [c1177c2] Simplify Python version handling in CI configuration
- [ef092a4] Correct root license text and reuse override for plan docs
- [b318ef9] Fix changelog generation for the very first release
- [bb1191b] Exclude development plans from the sphinx build
- [6d3bec7] Fix time format in configurationpre

### Refactoring

- [ea4ba1a] Migrate from Poetry to uv for package management
- [945093b] Remove link checking step from CI workflow
- [15b2b76] Modernize docs, updates, and bootstrap automation
- [f8a1b21] Use BOOTSTRAP_SCRIPT variable for script path

### Documentation

- [955895b] Switch template docs to sphinx
- [4db4bb1] Add release, changelog, and SPDX design
- [1633f49] Add release, changelog, and SPDX implementation plan
- [8100d77] Require new scripts to be committed executable
- [4853400] Fix the license source and reuse override in the plan
- [a374951] Document the --prepend duplicate-header caveat
- [a211f2d] Document the commit, license header, and release workflow

### Testing

- [563b414] Add tests for get_language function
- [e305fc9] Assert release and SPDX bootstrap substitution

### Build & CI

- [00c1e4c] Bump python in the docker-images group
- [28ee5e3] Bump the python-dependencies group with 3 updates
- [5825285] Bump urllib3 in the uv group across 1 directory
- [5729dcf] Bump actions/checkout from 4 to 6 in the github-actions group
- [14fbfde] Bump requests in the uv group across 1 directory
- [edd2cd4] Add validation tox tasks
- [06676db] Split validation workflows
- [79a3a40] Update readme coverage
- [06bab37] Publish GitHub Releases from version tags
- [e6a4053] Fix CI errors

### Chores

- [b502539] Bootstrap repository metadata
- [c342f66] Update file permissions for bootstrap_template.py
- [c52c267] Apply formatting
- [7dad4c6] Update dependencies
- [0383620] Remove mypy dependency and add pyrefly configuration
- [3700831] Remove python version configuration from CI bootstrap
- [3c288fc] Update workflow bootstrap
- [49d1640] Update file permissions for validate_distribution.py
- [4da8580] Apply yaml formatting
- [f5185c8] Update file permissions for update_coverage_readme.py
- [1690ab7] Apply mdformat to spec and plan docs

### Other

- [a300969] Initial commit
- [b1003be] Fix scripts
- [817f8f0] Add docs, .devcontainer and Dockerfile templates.
- [3f6b47d] Add CI GitHub action.
- [de9e2df] Fix README.md
- [f2e633a] Add .env configuration
- [4e2d8cd] Update README.md
