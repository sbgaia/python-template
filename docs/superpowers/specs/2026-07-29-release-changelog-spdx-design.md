# Release automation, changelog generation, and SPDX headers

Date: 2026-07-29

## Goal

Bring three capabilities from
[glacier-project/frost-planner](https://github.com/glacier-project/frost-planner)
into this template:

1. Tag-triggered GitHub Release publishing.
1. `CHANGELOG.md` generation from git history via git-cliff.
1. SPDX/REUSE licensing headers on source files.

Because this repository is a *template*, every added file must also survive
`scripts/bootstrap_template.py` — placeholders substituted, copyright holder
rewritten — and be covered by the template smoke test.

## Decisions

| Question                | Decision                                   | Rationale                                                                           |
| ----------------------- | ------------------------------------------ | ----------------------------------------------------------------------------------- |
| SPDX headers            | Auto-insert, then verify                   | The reference only lints; writing headers automatically removes the manual step.    |
| Changelog format        | Grouped by conventional-commit type        | This repository's history is consistently conventional, unlike the reference's.     |
| Release scope           | GitHub Release, with a commented PyPI stub | Works with no secrets in every generated repo; PyPI is opt-in.                      |
| Copyright holder        | `the <Project> contributors`               | Avoids editing a per-author name into every file as contributors change.            |
| Entrypoints             | Python scripts plus tox envs               | Matches this repo's all-Python `scripts/` and tox-driven convention; unit-testable. |
| Commit scope in bullets | Omitted                                    | Keeps bullets short; scope is recoverable from the hash.                            |
| Root `LICENSE`          | Kept alongside `LICENSES/`                 | GitHub license detection reads the root file.                                       |

## Divergences from the reference

These are deliberate improvements, not accidental drift.

- **`uv.lock` version sync.** `uv.lock` pins the project's own
  `version = "0.0.0"`. CI runs `uv run --locked`, so bumping only
  `pyproject.toml` would break every workflow on the release commit. The
  reference's `release.sh` does not handle this. `release.py` runs `uv lock`
  and `uv lock --check`, and commits the lockfile.
- **`git-cliff` as a pinned dependency.** The reference fetches it with
  unpinned `uvx`. Here it is a `dev` extra, so releases are reproducible.
- **Release artifacts are smoke-tested.** The release workflow runs
  `tox -e build`, reusing the existing `scripts/validate_distribution.py`,
  instead of a bare `uv build`.
- **Release notes come from git-cliff `--current`,** not an `awk` scrape of
  `CHANGELOG.md`, so notes cannot drift from a mis-parsed heading.
- **Template integration.** No equivalent exists upstream; the reference is
  not a template.

## 1. SPDX / REUSE layer

New files:

- `LICENSES/BSD-2-Clause.txt` — license text, copied from the existing root
  `LICENSE`.
- `REUSE.toml` — bulk annotations covering every non-Python tracked file.
- `scripts/add_spdx_headers.py` — wraps `reuse annotate`.

Two pre-commit hooks, in this order:

```yaml
- repo: local
  hooks:
  - id: reuse-annotate
    name: add SPDX headers
    entry: python scripts/add_spdx_headers.py
    language: python
    additional_dependencies: ['reuse>=6.2,<7']
    types: [python]
- repo: https://github.com/fsfe/reuse-tool
  rev: v6.2.0
  hooks:
  - id: reuse
```

`add_spdx_headers.py` invokes `reuse annotate` over the staged Python files
pre-commit passes as arguments, with:

```
--skip-existing --merge-copyrights --skip-unrecognised
-y <current year> -c "the <Project> contributors" -l BSD-2-Clause
```

`reuse` 6.2.0 requires Python >= 3.10, matching this template's
`requires-python = ">=3.10,<4"`.

### First-commit behavior

pre-commit fails any hook that modifies files — it compares file hashes and
ignores the hook's exit code. So the first `git commit` on a file with no
header aborts, with the header now written; re-running `git commit` succeeds.
This is the same behavior as `trailing-whitespace`. The benefit is never
hand-writing a header, not an uninterrupted commit.

`fail_fast: true` is already set globally, so the `reuse` lint hook does not
run in the same pass that `reuse-annotate` modifies files. It runs on the
retry.

### Header vs. bulk annotation

Inline headers go in non-empty tracked Python files only:

```
project_name/__init__.py          tests/test_bootstrap_template.py
project_name/greeter.py           tests/test_greeter.py
docs/conf.py                      tests/test_template_smoke.py
examples/say_hi.py                scripts/release.py
scripts/add_spdx_headers.py       scripts/gen_changelog.py
scripts/bootstrap_template.py
scripts/update_coverage_readme.py
scripts/validate_distribution.py
```

`tests/__init__.py` is 0 bytes and is deliberately excluded: `reuse lint`
skips zero-byte files, so annotating it would add content to an intentionally
empty file for no compliance gain. `add_spdx_headers.py` therefore skips
zero-byte inputs, matching `reuse lint`'s own behavior.

Everything else is covered by `REUSE.toml`, so non-Python files are never
rewritten. The annotation block covers exactly:

```toml
path = [
    ".devcontainer/**",
    ".env",
    ".github/**",
    ".gitignore",
    ".pre-commit-config.yaml",
    ".pylintrc",
    ".readthedocs.yaml",
    "AGENTS.md",
    "CHANGELOG.md",
    "CLAUDE.md",
    "CONTRIBUTING.md",
    "Dockerfile",
    "README.md",
    "cliff.toml",
    "docs/**",
    "pyproject.toml",
    "tox.ini",
    "uv.lock",
]
```

`docs/**` covers `docs/*.md` and this `docs/superpowers/specs/` directory.
`AGENTS.md` and `CLAUDE.md` are listed because they are untracked but *not*
gitignored, and `reuse lint` only skips VCS-ignored files — it would otherwise
flag them.

### Required `.gitignore` additions

`reuse lint` skips gitignored files, but `.ruff_cache/` and `.mypy_cache/`
are currently **not** ignored, so their contents would fail the lint. Both are
tool caches that belong in `.gitignore` regardless (`.mypy_cache` is a leftover
from before the pyrefly migration in `0383620`). Adding both entries is part of
this work — it is required for the hook to pass, not unrelated cleanup.

Verified against `reuse` 6.2.0 in a scratch repository: `reuse lint` ignores
the root `LICENSE`, the `LICENSES/` directory, `REUSE.toml` itself, and
zero-byte files. The root `LICENSE` therefore needs **no** `REUSE.toml` entry,
and the zero-byte skip above is confirmed behavior rather than an assumption.

`reuse annotate` writes this exact three-line form, preserving any shebang
above it:

```python
#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2026 the Python Template contributors
#
# SPDX-License-Identifier: BSD-2-Clause
```

Note the `#` separator line. The reference repository uses a compact two-line
header, which an older `reuse` produced. This design keeps the tool's native
output rather than post-processing it, so headers stay byte-identical to what
`reuse annotate` regenerates. The difference is cosmetic.

## 2. Changelog layer

`git-cliff>=2.13,<3` is added to the `dev` extra. It ships platform wheels on
PyPI that bundle the binary, so it resolves into `uv.lock` normally.

`cliff.toml`:

```toml
[changelog]
header = "# Changelog\n\n"
body = """
{% if version %}\
## {{ version | trim_start_matches(pat="v") }} - {{ timestamp | date(format="%Y-%m-%d") }}
{% else %}\
## Unreleased
{% endif %}
{% for group, commits in commits | group_by(attribute="group") %}
### {{ group | striptags | trim | upper_first }}

{% for commit in commits %}\
- [{{ commit.id | truncate(length=7, end="") }}] {{ commit.message | upper_first }}
{% endfor %}\
{% endfor %}\n
"""
trim = true
footer = ""

[git]
conventional_commits = true
filter_unconventional = false
split_commits = false
protect_breaking_commits = false
filter_commits = false
tag_pattern = "v[0-9]*"
topo_order = false
sort_commits = "oldest"
```

Commit parsers, in order — skips first, then type mapping, then a catch-all:

| Pattern                   | Group         |
| ------------------------- | ------------- |
| `^chore\(release\)`       | skipped       |
| `^Merge `                 | skipped       |
| `^feat`                   | Features      |
| `^fix`                    | Bug Fixes     |
| `^perf`                   | Performance   |
| `^refactor`               | Refactoring   |
| `^docs`                   | Documentation |
| `^test`                   | Testing       |
| `^(build\|ci)`            | Build & CI    |
| `^(chore\|style\|format)` | Chores        |
| `.*`                      | Other         |

Group names carry `<!-- N -->` numeric prefixes stripped by `striptags`. This
is git-cliff's documented idiom for forcing group order; `group_by` otherwise
sorts alphabetically.

`filter_unconventional = false` sends unconventional commits to *Other*
rather than dropping them.

Resulting format:

```markdown
## 0.1.0 - 2026-07-29

### Features

- [49157ab] add current_python_version function

### Bug Fixes

- [a3bd78d] run one tox Python env per matrix job
```

`CHANGELOG.md` is currently 0 bytes. `git-cliff --prepend` does not insert the
`[changelog] header`, so the file is seeded with `# Changelog\n\n` as part of
this work.

## 3. Release layer

### `scripts/gen_changelog.py`

Passes its arguments through to `git-cliff --config cliff.toml`. Preview to
stdout by default; `-o CHANGELOG.md` overwrites.

### `scripts/release.py X.Y.Z [--push] [--no-tag] [--dry-run]`

Same contract as the reference's `release.sh`, plus lockfile handling:

1. Validate `X.Y.Z` against `^\d+\.\d+\.\d+([.-].+)?$`; abort if the tag
   already exists or the working tree is dirty.
1. Resolve the previous reachable tag with
   `git describe --tags --abbrev=0 --match='v[0-9]*' HEAD`. If none, the
   changelog covers all history and a warning is printed.
1. Bump `version` in `pyproject.toml`.
1. Run `uv lock`, then `uv lock --check` to confirm the lockfile is in sync.
1. `git-cliff --config cliff.toml --tag vX.Y.Z <range> --prepend CHANGELOG.md`.
1. Commit `pyproject.toml`, `uv.lock`, and `CHANGELOG.md` as
   `chore(release): vX.Y.Z`.
1. Unless `--no-tag`, create annotated tag `vX.Y.Z`.
1. With `--push`, `git push origin HEAD --follow-tags`.

`--dry-run` prints the planned steps and exits without touching the tree, and
so does not require a clean tree.

### tox envs

`[testenv:changelog]` and `[testenv:release]`, both with
`runner = uv-venv-lock-runner`, `extras = dev`, and
`allowlist_externals = git, uv`.

Both are deliberately kept **out of** `env_list`. Every CI workflow invokes
tox as `tox run -e <env>`, but a developer running bare `uv run tox` locally
executes everything in `env_list` — which would fire a release attempt. Envs
outside `env_list` remain runnable via `tox run -e release`.

```
uv run tox run -e changelog
uv run tox run -e release -- 0.1.0 --push
```

### `.github/workflows/release.yaml`

Triggered by `push: tags: ['v*']`, with `permissions: contents: write`. Uses
the repository's own `./.github/actions/setup-python-uv` composite action
rather than inlining uv setup, matching the other workflows.

Steps:

1. `actions/checkout@v6` with `fetch-depth: 0` — git-cliff needs full history.
1. Verify the tag matches `pyproject.toml`'s version; fail with
   `::error::` if not.
1. `uv run --locked --extra dev tox run -e build` — builds sdist and wheel and
   import-smoke-tests the wheel via `scripts/validate_distribution.py`.
1. `git-cliff --config cliff.toml --current --strip header -o release-notes.md`;
   fail if the result is empty.
1. `softprops/action-gh-release@v2` with `body_path: release-notes.md` and
   `dist/*.whl`, `dist/*.tar.gz`.
1. A commented-out `publish` job — `needs: release`,
   `environment: pypi`, `permissions: id-token: write`,
   `pypa/gh-action-pypi-publish@release/v1` — with a comment explaining that
   enabling it requires configuring a PyPI Trusted Publisher.

## 4. Template integration

`scripts/bootstrap_template.py` changes:

- Add `PLACEHOLDER_COPYRIGHT = "the Python Template contributors"` beside the
  existing placeholders.
- Add `Path(".github/workflows/release.yaml")` to `WORKFLOW_FILES`, which
  feeds both `PACKAGE_FILES` and `REPOSITORY_FILES`.
- Add `cliff.toml`, `REUSE.toml`, `scripts/release.py`,
  `scripts/gen_changelog.py`, and `scripts/add_spdx_headers.py` to
  `PACKAGE_FILES` so `project_name` is substituted in them.
- Add `update_spdx_copyright()`, which rewrites
  `the Python Template contributors` to `the <Project Title> contributors` in
  `REUSE.toml` and in every inline header, and call it from `main()`.

The existing `PYTHON_VERSION_WORKFLOW_FILES` tuple is left unchanged:
`release.yaml` pins no Python version matrix.

## 5. Testing

- `tests/test_bootstrap_template.py` — `update_spdx_copyright()` rewrites
  `REUSE.toml` and inline headers; the newly added files are covered by
  placeholder substitution.
- `tests/test_release.py` — against a temporary git repository: version-format
  validation, refusal on an existing tag, refusal on a dirty tree,
  `pyproject.toml` bump, `uv.lock` version sync, commit message and tag
  creation, and `--dry-run` leaving the tree untouched.
- `tests/test_template_smoke.py` — the generated project has no
  `project_name` or `python-template` leftovers in the new files, and its
  headers name the generated project.

Manual verification before handing back:

- `pre-commit run --all-files` passes on a second run (first run writes
  headers).
- `uv run tox run -e changelog` produces sane grouped output against real
  history.
- `uv run tox run -e release -- 0.1.0 --dry-run` prints the expected plan.
- `uv lock --check` passes.

## Out of scope

- No separate `tox -e license` env. The pre-commit hook plus the existing
  `quality.yaml` pre-commit job already run REUSE checks in CI.
- No PyPI publishing enabled by default; the stub is commented out.
- No changes to existing workflows other than adding `release.yaml`.
