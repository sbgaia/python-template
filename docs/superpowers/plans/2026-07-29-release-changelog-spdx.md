# Release Automation, Changelog Generation, and SPDX Headers Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add tag-triggered GitHub Release publishing, git-cliff changelog generation, and auto-inserted SPDX/REUSE headers to this Python template, with all three surviving `scripts/bootstrap_template.py`.

**Architecture:** Three independent layers. The SPDX layer is two pre-commit hooks (a local fixer, then the upstream `reuse` linter) plus `REUSE.toml` for bulk-annotating non-Python files. The changelog layer is `cliff.toml` plus a thin `gen_changelog.py` wrapper. The release layer is `release.py` (version bump, lockfile sync, changelog prepend, commit, tag) driven locally via tox and consumed in CI by a tag-triggered workflow. A fourth task wires all of it into the template bootstrap script.

**Tech Stack:** Python 3.10+, uv, tox (`uv-venv-lock-runner`), pre-commit, `git-cliff>=2.13,<3`, `reuse>=6.2,<7`, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-07-29-release-changelog-spdx-design.md`

## Global Constraints

Every task's requirements implicitly include this section.

- Copyright holder string is exactly `the Python Template contributors`. License is exactly `BSD-2-Clause`.
- Ruff `line-length = 80`, `target-version = "py310"`. Ruff lint selects `D` (pydocstyle, Google convention) — **every module, function, and class outside `tests/` needs a docstring**. `tests/**/*.py` has `D` ignored.
- Ruff format uses `quote-style = "double"`.
- New scripts go in `scripts/`, are Python (not shell), start with `#!/usr/bin/env python3`, use `from __future__ import annotations`, and end with `raise SystemExit(main())`. Follow the existing style of `scripts/validate_distribution.py` and `scripts/bootstrap_template.py`.
- **Every new script in `scripts/` must be committed executable:** `chmod +x scripts/<name>.py` before `git add`. The `check-shebang-scripts-are-executable` pre-commit hook fails a shebang'd file that is not executable, and it reads the *git index* mode — so `git add --chmod=+x scripts/<name>.py` is the reliable form. All three existing `scripts/*.py` are mode `100755`. (`examples/say_hi.py` is `100644` because it has no shebang; do not add one.)
- All new `.py` files must carry the SPDX header shown in Task 1 verbatim, placed after any shebang and before the module docstring.
- `requires-python = ">=3.10,<4"`. `reuse` requires >=3.10, which matches.
- CI invokes tox only as `tox run -e <env>`. **Do not add `changelog` or `release` to `env_list`** — bare `uv run tox` would otherwise fire a release attempt.
- Commit messages are conventional (`feat:`, `fix:`, `docs:`, `build:`, `ci:`, `test:`, `chore:`), because `cliff.toml` parses them into changelog groups.
- Work on branch `feat/release-changelog-spdx`, which already exists and holds the spec.
- pre-commit is **not** installed as a git hook in this clone. Hooks do not run automatically on commit; run them explicitly with `uv run --extra dev pre-commit run --all-files` when a task says to.

---

### Task 1: SPDX / REUSE layer

**Files:**
- Create: `LICENSES/BSD-2-Clause.txt`
- Create: `REUSE.toml`
- Create: `scripts/add_spdx_headers.py`
- Test: `tests/test_add_spdx_headers.py`
- Modify: `.pre-commit-config.yaml` (append two repos before the trailing `exclude:` block)
- Modify: `.gitignore:51` (add two cache entries)
- Modify: all 12 non-empty tracked `.py` files (headers inserted by the tool, not by hand)

**Interfaces:**
- Consumes: nothing.
- Produces: `scripts/add_spdx_headers.py` exposing `annotatable(paths: list[str]) -> list[str]` and `build_command(paths: list[str], *, year: str, copyright_holder: str, license_id: str) -> list[str]`. `REUSE.toml` containing the literal string `the Python Template contributors` (Task 5 rewrites it). The header format Task 5's tests assert against.

- [ ] **Step 1: Create the LICENSES directory**

REUSE requires the license text under `LICENSES/`. The root `LICENSE` stays exactly where it is — GitHub's license detection reads it, and `reuse lint` ignores it.

```bash
mkdir -p LICENSES
cp LICENSE LICENSES/BSD-2-Clause.txt
```

- [ ] **Step 2: Write the failing test for `add_spdx_headers`**

Create `tests/test_add_spdx_headers.py`:

```python
import sys

from scripts.add_spdx_headers import annotatable, build_command


def test_annotatable_keeps_non_empty_files(tmp_path):
    populated = tmp_path / "populated.py"
    populated.write_text("x = 1\n", encoding="utf-8")

    assert annotatable([str(populated)]) == [str(populated)]


def test_annotatable_skips_zero_byte_files(tmp_path):
    empty = tmp_path / "__init__.py"
    empty.touch()

    assert annotatable([str(empty)]) == []


def test_annotatable_skips_missing_paths(tmp_path):
    assert annotatable([str(tmp_path / "absent.py")]) == []


def test_annotatable_skips_directories(tmp_path):
    assert annotatable([str(tmp_path)]) == []


def test_build_command_uses_reuse_annotate_with_skip_flags():
    command = build_command(
        ["pkg/mod.py"],
        year="2026",
        copyright_holder="the Python Template contributors",
        license_id="BSD-2-Clause",
    )

    assert command[:4] == [sys.executable, "-m", "reuse", "annotate"]
    assert "--skip-existing" in command
    assert "--merge-copyrights" in command
    assert "--skip-unrecognised" in command
    assert command[-1] == "pkg/mod.py"


def test_build_command_passes_copyright_metadata():
    command = build_command(
        ["pkg/mod.py"],
        year="2026",
        copyright_holder="the Acme contributors",
        license_id="BSD-2-Clause",
    )

    assert command[command.index("--year") + 1] == "2026"
    assert command[command.index("--copyright") + 1] == "the Acme contributors"
    assert command[command.index("--license") + 1] == "BSD-2-Clause"
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `uv run --extra dev pytest tests/test_add_spdx_headers.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.add_spdx_headers'`

- [ ] **Step 4: Write `scripts/add_spdx_headers.py`**

`--skip-existing` makes the hook idempotent; `--skip-unrecognised` stops it from failing on a file type `reuse` has no comment style for. Zero-byte files are filtered out because `reuse lint` ignores them, so annotating `tests/__init__.py` would add content to an intentionally empty file for no compliance gain.

```python
#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 the Python Template contributors
#
# SPDX-License-Identifier: BSD-2-Clause

"""Insert SPDX licensing headers into Python files that lack them."""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import date
from pathlib import Path

COPYRIGHT_HOLDER = "the Python Template contributors"
LICENSE_ID = "BSD-2-Clause"


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "paths",
        nargs="*",
        help="Files to annotate. Supplied by pre-commit.",
    )
    parser.add_argument(
        "--year",
        default=str(date.today().year),
        help="Copyright year to write. Defaults to the current year.",
    )
    parser.add_argument(
        "--copyright",
        default=COPYRIGHT_HOLDER,
        dest="copyright_holder",
        help="Copyright holder to write into the header.",
    )
    parser.add_argument(
        "--license",
        default=LICENSE_ID,
        dest="license_id",
        help="SPDX license identifier to write into the header.",
    )
    return parser.parse_args()


def annotatable(paths: list[str]) -> list[str]:
    """Return the paths reuse can annotate.

    Zero-byte files are skipped because ``reuse lint`` ignores them, so
    annotating them would add content to intentionally empty files without
    improving compliance.

    Args:
        paths: Candidate file paths.

    Returns:
        The subset of paths that are non-empty regular files.
    """
    keep = []
    for raw in paths:
        path = Path(raw)
        if path.is_file() and path.stat().st_size > 0:
            keep.append(raw)
    return keep


def build_command(
    paths: list[str],
    *,
    year: str,
    copyright_holder: str,
    license_id: str,
) -> list[str]:
    """Build the ``reuse annotate`` command for the given paths.

    Args:
        paths: Files to annotate.
        year: Copyright year to write.
        copyright_holder: Copyright holder to write.
        license_id: SPDX license identifier to write.

    Returns:
        The command as an argument list.
    """
    return [
        sys.executable,
        "-m",
        "reuse",
        "annotate",
        "--skip-existing",
        "--merge-copyrights",
        "--skip-unrecognised",
        "--year",
        year,
        "--copyright",
        copyright_holder,
        "--license",
        license_id,
        *paths,
    ]


def main() -> int:
    """Annotate the requested files and return the reuse exit status."""
    args = parse_args()
    paths = annotatable(args.paths)
    if not paths:
        return 0

    command = build_command(
        paths,
        year=args.year,
        copyright_holder=args.copyright_holder,
        license_id=args.license_id,
    )
    return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `uv run --extra dev pytest tests/test_add_spdx_headers.py -v`
Expected: PASS, 6 tests.

- [ ] **Step 6: Create `REUSE.toml`**

This covers every tracked non-Python file. `reuse lint` ignores the root `LICENSE`, `LICENSES/**`, `REUSE.toml` itself, and anything gitignored, so none of those are listed. `AGENTS.md`, `CLAUDE.md`, and `.claude/**` **are** listed: they are untracked but not gitignored, and `reuse lint` only skips VCS-ignored files. `docs/*.md` and `docs/superpowers/**` are used instead of `docs/**` so that `docs/conf.py` is covered by its inline header alone.

```toml
version = 1

[[annotations]]
path = [
    ".claude/**",
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
    "LICENSES/**",
    "README.md",
    "cliff.toml",
    "docs/*.md",
    "docs/superpowers/**",
    "pyproject.toml",
    "tox.ini",
    "uv.lock",
]
precedence = "aggregate"
SPDX-FileCopyrightText = "2026 the Python Template contributors"
SPDX-License-Identifier = "BSD-2-Clause"
```

- [ ] **Step 7: Add the missing cache entries to `.gitignore`**

`.ruff_cache/` and `.mypy_cache/` are currently not ignored, so `reuse lint` would fail on their contents. Insert both after `.pytest_cache/` on line 51, keeping the "Unit test / coverage reports" block alphabetically loose as it already is:

```
.pytest_cache/
.ruff_cache/
.mypy_cache/
cover/
```

- [ ] **Step 8: Register both pre-commit hooks**

Append to `.pre-commit-config.yaml` after the `ruff-pre-commit` repo block and before the trailing `# Global file exclusions` / `exclude:` block. Order matters: the fixer runs first, the linter verifies.

```yaml
  # SPDX headers: insert missing ones, then verify REUSE compliance
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

- [ ] **Step 9: Insert headers into every existing Python file**

Let the hook do it — do not hand-write headers. The first run reports failure because it modifies files; that is normal pre-commit behavior for a fixing hook.

Run: `uv run --extra dev pre-commit run reuse-annotate --all-files`
Expected: FAIL, reporting "files were modified by this hook".

Then confirm the format on a file that has a shebang and one that does not:

Run: `head -6 scripts/bootstrap_template.py project_name/greeter.py`

Expected — shebang preserved above the header, `#` separator line present, blank line before the docstring:

```python
#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2026 the Python Template contributors
#
# SPDX-License-Identifier: BSD-2-Clause

"""Bootstrap a repository created from this template."""
```

Confirm `tests/__init__.py` is still 0 bytes:

Run: `wc -c tests/__init__.py`
Expected: `0 tests/__init__.py`

- [ ] **Step 10: Verify full REUSE compliance and that nothing else broke**

Run: `uv run --extra dev pre-commit run --all-files`
Expected: PASS on every hook. If `reuse` reports missing licensing information, add the offending path to `REUSE.toml` and re-run.

Run: `uv run --extra dev pytest tests/ -q`
Expected: PASS. The inserted headers are comments and must not change behavior.

Run: `uv run --extra dev tox run -e type`
Expected: PASS.

- [ ] **Step 11: Commit**

```bash
chmod +x scripts/add_spdx_headers.py
git add --chmod=+x scripts/add_spdx_headers.py
git add LICENSES REUSE.toml tests/test_add_spdx_headers.py \
  .pre-commit-config.yaml .gitignore \
  project_name tests examples scripts docs/conf.py
git commit -m "feat(license): auto-insert and verify SPDX headers"
```

Before committing, confirm no unrelated file-mode changes are staged — `git diff --cached --summary` should show `mode change` only for files this task intentionally touched.

---

### Task 2: Changelog layer

**Files:**
- Create: `cliff.toml`
- Create: `scripts/gen_changelog.py`
- Modify: `CHANGELOG.md` (seed; currently 0 bytes)
- Modify: `pyproject.toml` (add `git-cliff` to the `dev` extra)
- Modify: `tox.ini` (add `[testenv:changelog]`, **not** to `env_list`)
- Modify: `uv.lock` (regenerated)
- Modify: `README.md`, `CONTRIBUTING.md` (document the env)

**Interfaces:**
- Consumes: the SPDX header format from Task 1.
- Produces: `cliff.toml` at the repo root, consumed by Task 3's `release.py` and Task 4's workflow via `--config cliff.toml`. `scripts/gen_changelog.py` passing `sys.argv[1:]` through to `git-cliff`.

- [ ] **Step 1: Add `git-cliff` to the dev extra**

It ships platform wheels on PyPI that bundle the Rust binary, so it resolves like any other dependency — no unpinned `uvx` fetch. Add to `[project.optional-dependencies] dev` in `pyproject.toml`, keeping the existing loose alphabetical-ish grouping (place it after `build` and before `hatchling`):

```toml
    "git-cliff>=2.13,<3",
```

Then relock:

```bash
uv lock
```

- [ ] **Step 2: Create `cliff.toml`**

This exact config was validated against this repository's real history — group ordering, the `striptags` prefix trick, and unconventional-commit retention all confirmed working with git-cliff 2.13.1. The trailing `\` on `{% endif %}` suppresses a duplicate blank line under the version heading.

```toml
# git-cliff configuration. Produces, per release:
#
#   ## VERSION - DATE
#
#   ### Group
#
#   - [shorthash] Subject
#
# Regenerate with `uv run tox run -e changelog -- -o CHANGELOG.md`.

[changelog]
header = "# Changelog\n\n"
body = """
{% if version %}\
## {{ version | trim_start_matches(pat="v") }} - {{ timestamp | date(format="%Y-%m-%d") }}
{% else %}\
## Unreleased
{% endif %}\
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
# Group names carry `<!-- N -->` prefixes purely to force ordering; the
# template strips them with `striptags`. Without them `group_by` sorts
# alphabetically.
commit_parsers = [
    { message = "^chore\\(release\\)", skip = true },
    { message = "^Merge ", skip = true },
    { message = "^feat", group = "<!-- 0 -->Features" },
    { message = "^fix", group = "<!-- 1 -->Bug Fixes" },
    { message = "^perf", group = "<!-- 2 -->Performance" },
    { message = "^refactor", group = "<!-- 3 -->Refactoring" },
    { message = "^docs", group = "<!-- 4 -->Documentation" },
    { message = "^test", group = "<!-- 5 -->Testing" },
    { message = "^(build|ci)", group = "<!-- 6 -->Build & CI" },
    { message = "^(chore|style|format)", group = "<!-- 7 -->Chores" },
    { message = ".*", group = "<!-- 8 -->Other" },
]
```

- [ ] **Step 3: Seed `CHANGELOG.md`**

`git-cliff --prepend` inserts only the rendered body, never the `[changelog] header`. The file is currently 0 bytes, so without seeding the first release would produce a changelog with no `# Changelog` title.

```bash
printf '# Changelog\n\n' > CHANGELOG.md
```

- [ ] **Step 4: Write `scripts/gen_changelog.py`**

```python
#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 the Python Template contributors
#
# SPDX-License-Identifier: BSD-2-Clause

"""Regenerate CHANGELOG.md from git history using the rules in cliff.toml."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

CONFIG = Path(__file__).resolve().parents[1] / "cliff.toml"


def build_command(argv: list[str]) -> list[str]:
    """Build the git-cliff command for the given passthrough arguments.

    Args:
        argv: Arguments forwarded verbatim to git-cliff.

    Returns:
        The command as an argument list.
    """
    return [
        sys.executable,
        "-m",
        "git_cliff",
        "--config",
        str(CONFIG),
        *argv,
    ]


def main() -> int:
    """Run git-cliff and return its exit status."""
    return subprocess.run(build_command(sys.argv[1:]), check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Verify the module entry point, and fall back if absent**

The `git-cliff` wheel may expose only a console script rather than an importable `git_cliff` module.

Run: `uv run --extra dev python -m git_cliff --version`
Expected: `git-cliff 2.13.x`

If that fails with `No module named git_cliff`, change `build_command` to invoke the console script from the same environment instead, and keep everything else identical:

```python
def build_command(argv: list[str]) -> list[str]:
    """Build the git-cliff command for the given passthrough arguments.

    Args:
        argv: Arguments forwarded verbatim to git-cliff.

    Returns:
        The command as an argument list.
    """
    executable = Path(sys.executable).parent / "git-cliff"
    return [str(executable), "--config", str(CONFIG), *argv]
```

- [ ] **Step 6: Add the tox env**

Add to `tox.ini` after `[testenv:build]`. Do **not** add `changelog` to `env_list` — bare `uv run tox` must not regenerate the changelog.

```ini
[testenv:changelog]
description = generate the changelog from git history
runner = uv-venv-lock-runner
extras = dev
allowlist_externals =
    git
commands =
    {envpython} scripts/gen_changelog.py {posargs}
```

- [ ] **Step 7: Verify the changelog renders correctly**

Run: `uv run --extra dev tox run -e changelog -- --tag v0.1.0`

Expected: grouped output on stdout, with `### Features` before `### Bug Fixes` before `### Refactoring`, exactly one blank line between the `## 0.1.0 - <today>` heading and the first `###` heading, and early non-conventional commits collected under `### Other`. `CHANGELOG.md` must be unchanged (no `-o` was passed).

Run: `git diff --stat CHANGELOG.md`
Expected: no output.

- [ ] **Step 8: Document the env**

In `README.md`, after the "Build and smoke-test the package artifacts" block (around line 113), and in `CONTRIBUTING.md` after its matching block (around line 56), add:

````markdown
Preview the generated changelog:

```bash
uv run tox -e changelog
```
````

Also add a row to the `README.md` repository-layout table (around line 167), matching the existing column alignment:

```
| `cliff.toml`    | Optional | git-cliff changelog generation rules.                                     |
```

And add to the README "Included tools" list:

```markdown
- [git-cliff](https://git-cliff.org/) for changelog generation
```

- [ ] **Step 9: Verify and commit**

Run: `uv run --extra dev pre-commit run --all-files`
Expected: PASS. `cliff.toml` and `CHANGELOG.md` are both covered by `REUSE.toml`, so `reuse` must stay green.

```bash
chmod +x scripts/gen_changelog.py
git add --chmod=+x scripts/gen_changelog.py
git add cliff.toml CHANGELOG.md pyproject.toml \
  uv.lock tox.ini README.md CONTRIBUTING.md
git commit -m "feat(changelog): generate CHANGELOG.md with git-cliff"
```

---

### Task 3: Release script

**Files:**
- Create: `scripts/release.py`
- Test: `tests/test_release.py`
- Modify: `tox.ini` (add `[testenv:release]`, **not** to `env_list`)
- Modify: `README.md`, `CONTRIBUTING.md`

**Interfaces:**
- Consumes: `cliff.toml` from Task 2, invoked as `git-cliff --config cliff.toml --tag <tag> <range> --prepend CHANGELOG.md`.
- Produces: `scripts/release.py` exposing `validate_version(version: str) -> str`, `tag_exists(tag: str, *, runner: Runner = run) -> bool`, `working_tree_dirty(*, runner: Runner = run) -> bool`, `previous_tag(*, runner: Runner = run) -> str | None`, `bump_pyproject(path: Path, version: str) -> None`, `sync_lockfile(*, runner: Runner = run) -> None`, and `changelog_range(prev: str | None) -> list[str]`. The commit subject format `chore(release): vX.Y.Z`, which `cliff.toml` skips via `^chore\(release\)` and Task 4's workflow relies on.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_release.py`. The `runner` seam keeps tests fast and offline — `sync_lockfile` is asserted on the commands it issues rather than by actually resolving dependencies. The git guards run against a real throwaway repo because that is cheap and catches real quoting bugs.

```python
import subprocess

import pytest

from scripts.release import (
    bump_pyproject,
    changelog_range,
    previous_tag,
    sync_lockfile,
    tag_exists,
    validate_version,
    working_tree_dirty,
)

PYPROJECT = """[project]
name = "project_name"
version = "0.0.0"
description = "A simple template project."
"""


class FakeRunner:
    """Records commands and replays canned results."""

    def __init__(self, results=None):
        self.commands = []
        self.results = results or {}

    def __call__(self, command, *, check=True, capture=False):
        self.commands.append(command)
        key = " ".join(command)
        result = self.results.get(key)
        if result is None:
            return subprocess.CompletedProcess(command, 0, "", "")
        return result


def git_repo(tmp_path):
    """Create a throwaway git repo with one commit."""
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "file.txt").write_text("hello\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "-c", "user.email=a@b", "-c", "user.name=a",
         "commit", "-qm", "init"],
        cwd=tmp_path,
        check=True,
    )
    return tmp_path


@pytest.mark.parametrize("version", ["0.1.0", "1.2.3", "10.0.1", "1.0.0-rc1"])
def test_validate_version_accepts_valid_versions(version):
    assert validate_version(version) == version


@pytest.mark.parametrize("version", ["1.2", "v1.2.3", "abc", "", "1.2.3-"])
def test_validate_version_rejects_invalid_versions(version):
    with pytest.raises(ValueError):
        validate_version(version)


def test_bump_pyproject_replaces_version(tmp_path):
    path = tmp_path / "pyproject.toml"
    path.write_text(PYPROJECT, encoding="utf-8")

    bump_pyproject(path, "0.1.0")

    assert 'version = "0.1.0"' in path.read_text(encoding="utf-8")
    assert 'version = "0.0.0"' not in path.read_text(encoding="utf-8")


def test_bump_pyproject_leaves_other_metadata_alone(tmp_path):
    path = tmp_path / "pyproject.toml"
    path.write_text(PYPROJECT, encoding="utf-8")

    bump_pyproject(path, "0.1.0")

    content = path.read_text(encoding="utf-8")
    assert 'name = "project_name"' in content
    assert 'description = "A simple template project."' in content


def test_bump_pyproject_raises_without_a_version_line(tmp_path):
    path = tmp_path / "pyproject.toml"
    path.write_text('[project]\nname = "x"\n', encoding="utf-8")

    with pytest.raises(ValueError):
        bump_pyproject(path, "0.1.0")


def test_tag_exists_is_false_for_unknown_tag(tmp_path, monkeypatch):
    monkeypatch.chdir(git_repo(tmp_path))

    assert tag_exists("v9.9.9") is False


def test_tag_exists_is_true_for_created_tag(tmp_path, monkeypatch):
    repo = git_repo(tmp_path)
    subprocess.run(["git", "tag", "-a", "v0.1.0", "-m", "v0.1.0"],
                   cwd=repo, check=True)
    monkeypatch.chdir(repo)

    assert tag_exists("v0.1.0") is True


def test_working_tree_dirty_is_false_when_clean(tmp_path, monkeypatch):
    monkeypatch.chdir(git_repo(tmp_path))

    assert working_tree_dirty() is False


def test_working_tree_dirty_is_true_with_modifications(tmp_path, monkeypatch):
    repo = git_repo(tmp_path)
    (repo / "file.txt").write_text("changed\n", encoding="utf-8")
    monkeypatch.chdir(repo)

    assert working_tree_dirty() is True


def test_previous_tag_is_none_without_tags(tmp_path, monkeypatch):
    monkeypatch.chdir(git_repo(tmp_path))

    assert previous_tag() is None


def test_previous_tag_returns_most_recent_reachable_tag(tmp_path, monkeypatch):
    repo = git_repo(tmp_path)
    subprocess.run(["git", "tag", "-a", "v0.1.0", "-m", "v0.1.0"],
                   cwd=repo, check=True)
    monkeypatch.chdir(repo)

    assert previous_tag() == "v0.1.0"


def test_sync_lockfile_locks_then_verifies():
    runner = FakeRunner()

    sync_lockfile(runner=runner)

    assert runner.commands == [["uv", "lock"], ["uv", "lock", "--check"]]


def test_changelog_range_is_empty_without_a_previous_tag():
    assert changelog_range(None) == []


def test_changelog_range_spans_from_previous_tag_to_head():
    assert changelog_range("v0.1.0") == ["v0.1.0..HEAD"]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run --extra dev pytest tests/test_release.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.release'`

- [ ] **Step 3: Write `scripts/release.py`**

`sync_lockfile` is the piece the reference repo's `release.sh` is missing. `uv.lock` pins the project's own version, and CI runs `uv run --locked`, so a release that bumps only `pyproject.toml` breaks every workflow on the release commit.

```python
#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 the Python Template contributors
#
# SPDX-License-Identifier: BSD-2-Clause

"""Prepare a release: bump the version, changelog, commit, and tag.

The release workflow at ``.github/workflows/release.yaml`` picks up the
pushed tag and publishes a GitHub Release with the matching CHANGELOG
section.

Usage:
    scripts/release.py X.Y.Z             # bump + commit + tag (no push)
    scripts/release.py X.Y.Z --push      # also push branch and tag
    scripts/release.py X.Y.Z --dry-run   # show what would happen
    scripts/release.py X.Y.Z --no-tag    # commit only, skip the tag
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Callable

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG = REPO_ROOT / "cliff.toml"
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+(?:[.-][0-9A-Za-z.-]+)?$")
VERSION_LINE = re.compile(r'^version\s*=\s*"[^"]*"', re.MULTILINE)

Runner = Callable[..., subprocess.CompletedProcess]


def run(
    command: list[str],
    *,
    check: bool = True,
    capture: bool = False,
) -> subprocess.CompletedProcess:
    """Run a command, optionally capturing its output.

    Args:
        command: The command and its arguments.
        check: Raise on a non-zero exit status.
        capture: Capture stdout and stderr as text.

    Returns:
        The completed process.
    """
    return subprocess.run(
        command,
        check=check,
        capture_output=capture,
        text=True,
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("version", help="Release version, as X.Y.Z.")
    parser.add_argument(
        "--push",
        action="store_true",
        help="Push the release commit and tag to origin.",
    )
    parser.add_argument(
        "--no-tag",
        action="store_true",
        help="Create the release commit without an annotated tag.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned steps without modifying anything.",
    )
    return parser.parse_args()


def validate_version(version: str) -> str:
    """Validate a release version string.

    Args:
        version: Candidate version.

    Returns:
        The version unchanged.

    Raises:
        ValueError: If the version is not of the form X.Y.Z.
    """
    if not VERSION_PATTERN.fullmatch(version):
        raise ValueError(
            f"'{version}' is not a valid version (expected X.Y.Z)."
        )
    return version


def tag_exists(tag: str, *, runner: Runner = run) -> bool:
    """Return whether a git tag already exists.

    Args:
        tag: Tag name to look for.
        runner: Command runner, injectable for tests.

    Returns:
        True if the tag resolves.
    """
    result = runner(
        ["git", "rev-parse", "--verify", f"refs/tags/{tag}"],
        check=False,
        capture=True,
    )
    return result.returncode == 0


def working_tree_dirty(*, runner: Runner = run) -> bool:
    """Return whether the working tree has uncommitted changes.

    Args:
        runner: Command runner, injectable for tests.

    Returns:
        True if tracked files differ from HEAD.
    """
    result = runner(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        capture=True,
    )
    return bool(result.stdout.strip())


def previous_tag(*, runner: Runner = run) -> str | None:
    """Return the most recent version tag reachable from HEAD.

    Tags on unrelated branches are skipped automatically.

    Args:
        runner: Command runner, injectable for tests.

    Returns:
        The tag name, or None when no version tag is reachable.
    """
    result = runner(
        [
            "git",
            "describe",
            "--tags",
            "--abbrev=0",
            "--match=v[0-9]*",
            "HEAD",
        ],
        check=False,
        capture=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def changelog_range(prev: str | None) -> list[str]:
    """Return the git-cliff commit range arguments.

    Args:
        prev: The previous release tag, if any.

    Returns:
        A single-element range list, or an empty list for full history.
    """
    if prev is None:
        return []
    return [f"{prev}..HEAD"]


def bump_pyproject(path: Path, version: str) -> None:
    """Rewrite the project version in pyproject.toml.

    Args:
        path: Path to pyproject.toml.
        version: New version string.

    Raises:
        ValueError: If no version line is present.
    """
    content = path.read_text(encoding="utf-8")
    updated, count = VERSION_LINE.subn(
        f'version = "{version}"',
        content,
        count=1,
    )
    if count == 0:
        raise ValueError(f"No version line found in {path}.")
    path.write_text(updated, encoding="utf-8")


def sync_lockfile(*, runner: Runner = run) -> None:
    """Refresh uv.lock for the new version and verify it is in sync.

    uv.lock pins the project's own version, and CI runs with ``--locked``,
    so the lockfile must be regenerated alongside pyproject.toml.

    Args:
        runner: Command runner, injectable for tests.
    """
    runner(["uv", "lock"])
    runner(["uv", "lock", "--check"])


def generate_changelog(tag: str, prev: str | None) -> None:
    """Prepend the new release section to CHANGELOG.md.

    Args:
        tag: The release tag, including the leading 'v'.
        prev: The previous release tag, if any.
    """
    run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "gen_changelog.py"),
            "--tag",
            tag,
            *changelog_range(prev),
            "--prepend",
            "CHANGELOG.md",
        ]
    )


def main() -> int:
    """Run the release preparation process."""
    args = parse_args()
    version = validate_version(args.version)
    tag = f"v{version}"

    if tag_exists(tag):
        raise SystemExit(f"error: tag {tag} already exists")

    prev = previous_tag()
    if prev is None:
        print(
            "warning: no previous tag reachable; the changelog will cover "
            "all history",
            file=sys.stderr,
        )
    else:
        print(f"Previous reachable tag: {prev}")

    if args.dry_run:
        print(f"[dry-run] bump pyproject.toml to {version}")
        print("[dry-run] uv lock && uv lock --check")
        print(
            "[dry-run] prepend CHANGELOG.md "
            f"({prev + '..HEAD' if prev else 'full history'})"
        )
        print(f"[dry-run] commit: chore(release): {tag}")
        if not args.no_tag:
            print(f"[dry-run] create annotated tag {tag}")
        if args.push:
            print("[dry-run] push branch and tag")
        return 0

    if working_tree_dirty():
        raise SystemExit(
            "error: working tree has uncommitted changes; commit or stash "
            "them first"
        )

    print(f"Preparing release: {tag}")
    bump_pyproject(REPO_ROOT / "pyproject.toml", version)
    sync_lockfile()
    generate_changelog(tag, prev)

    run(["git", "add", "pyproject.toml", "uv.lock", "CHANGELOG.md"])
    run(["git", "commit", "-m", f"chore(release): {tag}"])

    if not args.no_tag:
        run(["git", "tag", "-a", tag, "-m", tag])

    if args.push:
        run(["git", "push", "origin", "HEAD", "--follow-tags"])
        print(f"\nPushed {tag}. The release workflow will publish it.")
    else:
        print(f"\nCreated commit and tag {tag} locally.")
        print("Push with: git push origin HEAD --follow-tags")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run --extra dev pytest tests/test_release.py -v`
Expected: PASS, 19 tests (the two parametrized cases contribute 4 and 5).

- [ ] **Step 5: Add the tox env**

Add to `tox.ini` after `[testenv:changelog]`. Again, **not** in `env_list`.

```ini
[testenv:release]
description = prepare a release commit and tag
runner = uv-venv-lock-runner
extras = dev
allowlist_externals =
    git
    uv
commands =
    {envpython} scripts/release.py {posargs}
```

- [ ] **Step 6: Verify the dry run against the real repository**

Run: `uv run --extra dev tox run -e release -- 0.1.0 --dry-run`

Expected: the warning about no reachable tag (this repo has no `v*` tags yet), then the five `[dry-run]` lines. Confirm nothing changed:

Run: `git status --porcelain`
Expected: no `pyproject.toml`, `uv.lock`, or `CHANGELOG.md` entries.

Also confirm the guard works:

Run: `uv run --extra dev tox run -e release -- 1.2 --dry-run`
Expected: FAIL with `'1.2' is not a valid version (expected X.Y.Z).`

- [ ] **Step 7: Document the env**

Add to `README.md` and `CONTRIBUTING.md`, after the changelog block from Task 2:

````markdown
Prepare a release — bumps the version, regenerates the changelog, commits,
and tags:

```bash
uv run tox -e release -- 0.1.0
uv run tox -e release -- 0.1.0 --push
```

Pushing the tag triggers the `Release` workflow, which builds the
distributions and publishes a GitHub Release.
````

- [ ] **Step 8: Verify and commit**

Run: `uv run --extra dev pre-commit run --all-files`
Expected: PASS.

Run: `uv run --extra dev pytest tests/ -q`
Expected: PASS.

```bash
chmod +x scripts/release.py
git add --chmod=+x scripts/release.py
git add tests/test_release.py tox.ini README.md CONTRIBUTING.md
git commit -m "feat(release): add release preparation script"
```

---

### Task 4: Release workflow

**Files:**
- Create: `.github/workflows/release.yaml`

`README.md` needs no change here: it documents tox envs and the repository
layout, but has no per-workflow list to extend. The release *command* is
documented in Task 3, Step 7.

**Interfaces:**
- Consumes: `cliff.toml` (Task 2), the `chore(release): vX.Y.Z` commit and `vX.Y.Z` tag convention (Task 3), the existing `./.github/actions/setup-python-uv` composite action, and the existing `[testenv:build]` env which runs `scripts/validate_distribution.py`.
- Produces: `.github/workflows/release.yaml`, which Task 5 adds to `WORKFLOW_FILES`.

- [ ] **Step 1: Create the workflow**

Two deliberate improvements over the reference: step 3 runs `tox -e build` rather than a bare `uv build`, reusing the existing `validate_distribution.py` so the published wheel is import-smoke-tested; and step 4 derives notes from git via `git-cliff --current` rather than scraping `CHANGELOG.md` with `awk`, which cannot drift from a mis-parsed heading.

`fetch-depth: 0` is required — git-cliff needs full history and tags.

```yaml
name: Release

on:
  push:
    tags:
    - v*

permissions:
  contents: read

env:
  PYTHON_VERSION: '3.10'

jobs:
  release:
    name: Publish GitHub Release
    runs-on: ubuntu-latest
    timeout-minutes: 20
    permissions:
      contents: write
    steps:
    - uses: actions/checkout@v6
      with:
        fetch-depth: 0
    - uses: ./.github/actions/setup-python-uv
      with:
        python-version: ${{ env.PYTHON_VERSION }}
    # tomllib is 3.11+, and PYTHON_VERSION is 3.10 to match this template's
    # floor, so the version is read with a regex instead. The pattern mirrors
    # VERSION_LINE in scripts/release.py, which writes this same line.
    - name: Verify tag matches the project version
      run: |
        tag_version="${GITHUB_REF_NAME#v}"
        project_version=$(uv run --locked python -c \
          "import pathlib, re; print(re.search(r'(?m)^version\s*=\s*\"([^\"]+)\"', pathlib.Path('pyproject.toml').read_text()).group(1))")
        if [ "$tag_version" != "$project_version" ]; then
          echo "::error::Tag $GITHUB_REF_NAME does not match pyproject.toml version $project_version"
          exit 1
        fi
    - name: Build and verify package artifacts
      run: uv run --locked --extra dev tox run -e build
    - name: Extract release notes
      run: |
        uv run --locked --extra dev python scripts/gen_changelog.py \
          --current --strip header -o release-notes.md
        if [ ! -s release-notes.md ]; then
          echo "::error::No changelog content found for $GITHUB_REF_NAME"
          exit 1
        fi
        cat release-notes.md
    - name: Create GitHub Release
      uses: softprops/action-gh-release@v2
      with:
        name: ${{ github.ref_name }}
        body_path: release-notes.md
        files: |
          dist/*.whl
          dist/*.tar.gz
        draft: false
        prerelease: false

  # Publishing to PyPI is opt-in. To enable it:
  #   1. Create a PyPI Trusted Publisher for this repository, pointing at
  #      workflow `release.yaml` and environment `pypi`.
  #      See https://docs.pypi.org/trusted-publishers/
  #   2. Create a GitHub environment named `pypi`.
  #   3. Uncomment the job below.
  # No API token is needed; authentication uses OIDC.
  #
  # publish:
  #   name: Publish to PyPI
  #   needs: release
  #   runs-on: ubuntu-latest
  #   timeout-minutes: 15
  #   environment: pypi
  #   permissions:
  #     id-token: write
  #   steps:
  #   - uses: actions/checkout@v6
  #   - uses: ./.github/actions/setup-python-uv
  #     with:
  #       python-version: ${{ env.PYTHON_VERSION }}
  #   - name: Build distributions
  #     run: uv run --locked --extra dev tox run -e build
  #   - name: Publish
  #     uses: pypa/gh-action-pypi-publish@release/v1
```

- [ ] **Step 2: Verify the workflow parses and matches repo conventions**

Run: `uv run --extra dev pre-commit run --all-files --files .github/workflows/release.yaml`

Expected: PASS. `check-yaml` validates syntax and `pretty-format-yaml` enforces 2-space indentation — if it reformats the file, accept its output and re-run.

Confirm the referenced tox env and composite action exist:

Run: `uv run --extra dev tox list | grep build && ls .github/actions/setup-python-uv/action.yaml`
Expected: the `build` env is listed and the action file exists.

- [ ] **Step 3: Verify the release-notes command works locally**

This is the one workflow step that can be exercised without pushing a tag. `--current` needs a tag to resolve, so create a throwaway one, then delete it.

```bash
git tag -a v0.0.1-test -m v0.0.1-test
uv run --extra dev python scripts/gen_changelog.py --current --strip header
git tag -d v0.0.1-test
```

Expected: a `## 0.0.1-test - <today>` section with grouped bullets and no `# Changelog` header line. Confirm the tag is gone afterwards with `git tag -l`.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/release.yaml
git commit -m "ci(release): publish GitHub Releases from version tags"
```

---

### Task 5: Template bootstrap integration

**Files:**
- Modify: `scripts/bootstrap_template.py` (placeholder constants, `WORKFLOW_FILES`, `PACKAGE_FILES`, new `update_spdx_copyright`, `main`)
- Test: `tests/test_bootstrap_template.py` (extend)

**Interfaces:**
- Consumes: `REUSE.toml` and the header format (Task 1), `cliff.toml` and `scripts/gen_changelog.py` (Task 2), `scripts/release.py` (Task 3), `.github/workflows/release.yaml` (Task 4).
- Produces: `PLACEHOLDER_COPYRIGHT` and `update_spdx_copyright(paths, *, project_title, dry_run)`, relied on by Task 6's smoke assertions.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_bootstrap_template.py`. Import `update_spdx_copyright` and `PLACEHOLDER_COPYRIGHT` by extending the existing `from scripts.bootstrap_template import (...)` block at the top of the file.

```python
SPDX_HEADER = (
    "# SPDX-FileCopyrightText: 2026 the Python Template contributors\n"
    "#\n"
    "# SPDX-License-Identifier: BSD-2-Clause\n"
    "\n"
    '"""Module."""\n'
)
REUSE_TOML = (
    "version = 1\n"
    "\n"
    "[[annotations]]\n"
    'path = ["README.md"]\n'
    'precedence = "aggregate"\n'
    'SPDX-FileCopyrightText = "2026 the Python Template contributors"\n'
    'SPDX-License-Identifier = "BSD-2-Clause"\n'
)


def test_update_spdx_copyright_rewrites_inline_headers(tmp_path):
    module = tmp_path / "mod.py"
    module.write_text(SPDX_HEADER, encoding="utf-8")

    update_spdx_copyright(
        [module],
        project_title="Acme Tool",
        dry_run=False,
    )

    content = module.read_text(encoding="utf-8")
    assert "2026 the Acme Tool contributors" in content
    assert PLACEHOLDER_COPYRIGHT not in content


def test_update_spdx_copyright_rewrites_reuse_toml(tmp_path):
    reuse_toml = tmp_path / "REUSE.toml"
    reuse_toml.write_text(REUSE_TOML, encoding="utf-8")

    update_spdx_copyright(
        [reuse_toml],
        project_title="Acme Tool",
        dry_run=False,
    )

    content = reuse_toml.read_text(encoding="utf-8")
    assert 'SPDX-FileCopyrightText = "2026 the Acme Tool contributors"' in content


def test_update_spdx_copyright_preserves_license_identifier(tmp_path):
    module = tmp_path / "mod.py"
    module.write_text(SPDX_HEADER, encoding="utf-8")

    update_spdx_copyright(
        [module],
        project_title="Acme Tool",
        dry_run=False,
    )

    content = module.read_text(encoding="utf-8")
    assert "# SPDX-License-Identifier: BSD-2-Clause" in content


def test_update_spdx_copyright_dry_run_leaves_files_untouched(tmp_path):
    module = tmp_path / "mod.py"
    module.write_text(SPDX_HEADER, encoding="utf-8")

    update_spdx_copyright(
        [module],
        project_title="Acme Tool",
        dry_run=True,
    )

    assert module.read_text(encoding="utf-8") == SPDX_HEADER


def test_update_spdx_copyright_ignores_missing_files(tmp_path):
    update_spdx_copyright(
        [tmp_path / "absent.py"],
        project_title="Acme Tool",
        dry_run=False,
    )


def test_release_workflow_is_a_bootstrap_target():
    from scripts.bootstrap_template import WORKFLOW_FILES

    assert Path(".github/workflows/release.yaml") in WORKFLOW_FILES


def test_spdx_files_cover_the_new_automation_scripts():
    from scripts.bootstrap_template import SPDX_FILES

    for path in (
        Path("REUSE.toml"),
        Path("scripts/release.py"),
        Path("scripts/gen_changelog.py"),
        Path("scripts/add_spdx_headers.py"),
    ):
        assert path in SPDX_FILES
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run --extra dev pytest tests/test_bootstrap_template.py -v -k "spdx or workflow_is_a_bootstrap or automation_files"`
Expected: FAIL — `ImportError: cannot import name 'update_spdx_copyright'`

- [ ] **Step 3: Add the placeholder constant**

In `scripts/bootstrap_template.py`, after `PLACEHOLDER_DESCRIPTION`:

```python
PLACEHOLDER_COPYRIGHT = "the Python Template contributors"
```

- [ ] **Step 4: Register the new files**

Add `Path(".github/workflows/release.yaml")` to `WORKFLOW_FILES`, keeping alphabetical order (after `quality.yaml`). It feeds both `PACKAGE_FILES` and `REPOSITORY_FILES` via the existing splat.

Do **not** add `cliff.toml`, `REUSE.toml`, or the three new scripts to `PACKAGE_FILES`. `PACKAGE_FILES` exists to substitute the literal strings `project_name` and `python-template`, and none of those files contain either — registering them there would be a no-op that misleads the next reader. Their only template-varying content is the SPDX copyright holder, handled by `SPDX_FILES` below.

Leave `PYTHON_VERSION_WORKFLOW_FILES` unchanged — `release.yaml` has a `PYTHON_VERSION` env var but no version matrix, and `update_ci_workflow` would be a no-op beyond that single substitution. This means the release workflow keeps `PYTHON_VERSION: '3.10'` even when a generated project raises its minimum; that is harmless because the release build is version-independent, and 3.10 is deliberate given the `tomllib` constraint noted in Task 4.

Add a module-level tuple listing every file carrying the copyright string, after `REPOSITORY_FILES`:

```python
SPDX_FILES = (
    Path("REUSE.toml"),
    Path("docs/conf.py"),
    Path("examples/say_hi.py"),
    Path("scripts/add_spdx_headers.py"),
    Path("scripts/bootstrap_template.py"),
    Path("scripts/gen_changelog.py"),
    Path("scripts/release.py"),
    Path("scripts/update_coverage_readme.py"),
    Path("scripts/validate_distribution.py"),
    Path("tests/test_add_spdx_headers.py"),
    Path("tests/test_bootstrap_template.py"),
    Path("tests/test_greeter.py"),
    Path("tests/test_release.py"),
    Path("tests/test_template_smoke.py"),
)
```

The package's own `.py` files are handled separately in Step 6, because the package directory gets renamed.

- [ ] **Step 5: Write `update_spdx_copyright`**

Add after `update_readme`:

```python
def update_spdx_copyright(
    paths: list[Path],
    *,
    project_title: str,
    dry_run: bool,
) -> None:
    """Rewrite the SPDX copyright holder in the given files.

    Args:
        paths: Files that may contain the placeholder copyright holder.
        project_title: Human-readable project title.
        dry_run: Print planned changes without writing them.
    """
    holder = f"the {project_title} contributors"
    for path in paths:
        replace_text(
            path,
            {PLACEHOLDER_COPYRIGHT: holder},
            dry_run=dry_run,
        )
```

`replace_text` already skips missing files and prints `updated <path>`, which satisfies the missing-file test.

- [ ] **Step 6: Call it from `main`**

Insert immediately **before** `rename_package_dir(...)` at the end of `main()`, so the package files are still at their placeholder path when rewritten:

```python
    update_spdx_copyright(
        [
            *SPDX_FILES,
            *sorted(PACKAGE_DIR.glob("*.py")),
        ],
        project_title=project_title,
        dry_run=args.dry_run,
    )
    rename_package_dir(package_name, dry_run=args.dry_run)
```

- [ ] **Step 7: Run the tests to verify they pass**

Run: `uv run --extra dev pytest tests/test_bootstrap_template.py -v`
Expected: PASS, including the pre-existing tests.

- [ ] **Step 8: Verify bootstrap end-to-end with a dry run**

Run: `uv run --extra dev python scripts/bootstrap_template.py acme-tool --dry-run`

Expected: an `updated <path>` line for each entry in `SPDX_FILES` plus each `project_name/*.py`, alongside the pre-existing output. `cliff.toml` will **not** appear — it carries no copyright header (it is covered by the `REUSE.toml` bulk annotation) and no `project_name` placeholder. `.github/workflows/release.yaml` will also not appear, for the same reason: it is in `WORKFLOW_FILES` for consistency but contains neither placeholder string. Confirm nothing was written:

Run: `git status --porcelain`
Expected: no modifications.

- [ ] **Step 9: Verify and commit**

Run: `uv run --extra dev pre-commit run --all-files`
Expected: PASS.

```bash
git add scripts/bootstrap_template.py tests/test_bootstrap_template.py
git commit -m "feat(bootstrap): substitute SPDX and release metadata"
```

---

### Task 6: Template smoke test coverage

**Files:**
- Modify: `tests/test_template_smoke.py:22-42` (`PLACEHOLDER_CHECK_PATHS`) and `tests/test_template_smoke.py:70-121` (the single smoke test)

**Interfaces:**
- Consumes: everything from Tasks 1-5, exercised through the real `bootstrap_template.py` run the smoke test already performs.
- Produces: nothing consumed downstream.

The smoke test is a single test — `test_generated_project_bootstraps_and_builds(tmp_path)` at line 70 — that copytrees the repo, runs `bootstrap_template.py demo-service`, syncs, builds, and finally loops over the `PLACEHOLDER_CHECK_PATHS` tuple (line 22) asserting no leftover placeholders. Extend those two existing structures; do not add a second harness or invent a fixture.

Because bootstrap is invoked with `demo-service` and no `--project-title`, `resolve_metadata` derives the title `Demo Service`, so the expected copyright holder is exactly `the Demo Service contributors`.

- [ ] **Step 1: Extend `PLACEHOLDER_CHECK_PATHS`**

Add these six entries, preserving the tuple's existing alphabetical grouping (workflow paths first, then root and subdirectory files):

```python
    ".github/workflows/release.yaml",
    "REUSE.toml",
    "cliff.toml",
    "scripts/add_spdx_headers.py",
    "scripts/gen_changelog.py",
    "scripts/release.py",
```

- [ ] **Step 2: Add the SPDX assertions to the existing test**

Append to the end of `test_generated_project_bootstraps_and_builds`, immediately after the existing `for relative_path in PLACEHOLDER_CHECK_PATHS:` loop:

```python
    reuse_toml = (generated_repo / "REUSE.toml").read_text(encoding="utf-8")
    assert "the Demo Service contributors" in reuse_toml
    assert "the Python Template contributors" not in reuse_toml

    package_modules = sorted(
        path
        for path in (generated_repo / "demo_service").glob("*.py")
        if path.stat().st_size > 0
    )
    assert package_modules

    for module in package_modules:
        content = module.read_text(encoding="utf-8")
        assert "SPDX-License-Identifier: BSD-2-Clause" in content, str(module)
        assert "the Demo Service contributors" in content, str(module)
        assert "the Python Template contributors" not in content, str(module)
```

- [ ] **Step 3: Run the smoke test**

The suite is gated behind an environment variable.

Run: `RUN_TEMPLATE_SMOKE=1 uv run --extra dev --extra docs pytest tests/test_template_smoke.py -v`

Expected: PASS. If the copyright assertions fail, a path is missing from `SPDX_FILES` in Task 5 — add it there rather than weakening the test. If `uv sync --locked` fails, `uv.lock` was not committed after adding `git-cliff` in Task 2.

- [ ] **Step 4: Run it the way CI does**

Run: `uv run --locked --extra dev --extra docs tox run -e template`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_template_smoke.py
git commit -m "test(template): assert release and SPDX bootstrap substitution"
```

---

### Task 7: Full verification

**Files:** none modified unless a check fails.

**Interfaces:**
- Consumes: Tasks 1-6.
- Produces: nothing.

- [ ] **Step 1: Run every quality gate CI runs**

Run each and confirm PASS:

```bash
uv run --locked --extra dev pre-commit run --all-files
uv run --locked --extra dev tox run -e type
uv run --locked --extra dev tox run -e coverage
uv run --locked --extra dev tox run -e build
uv lock --check
```

`coverage` enforces `fail_under = 90` on the `project_name` package only, so the new scripts do not affect it.

- [ ] **Step 2: Confirm the release and changelog envs stayed out of the default set**

Run: `uv run --extra dev tox list --no-desc`

Expected: `changelog` and `release` appear in the output, but under the "additional environments" section rather than the default list. Cross-check by confirming `env_list` in `tox.ini` contains neither name.

- [ ] **Step 3: Confirm the changelog covers the release commits themselves**

Run: `uv run --extra dev tox run -e changelog -- --tag v0.1.0`

Expected: every commit from this plan appears under the group its type maps to — the three `feat:` commits under `Features`, the `ci:` commit under `Build & CI`, the `test:` commit under `Testing`, and the `docs:` spec and plan commits under `Documentation`.

- [ ] **Step 4: Report results**

Report the actual command output for each gate. If any failed, say so with the output rather than describing the work as complete.
