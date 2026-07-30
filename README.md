# Python Template

<!-- coverage:start -->

![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)

Current coverage: **100.00%**. Required minimum: **90.00%**.

Coverage details: 30/30 statements and 6/6 branches covered.
CI updates this block from `coverage.xml` after the coverage workflow runs.

<!-- coverage:end -->

This repository is a Python project template for the Glacier project. It gives
new projects a working package layout, uv-based dependency management, tests,
Ruff formatting and linting, Pyrefly type checking, Sphinx documentation,
Docker support, and GitHub Actions workflows.

## Create a project from the template

Create a new repository with GitHub's **Use this template** button. The
`Bootstrap Template` workflow attempts to rewrite the template placeholders on
the first run and commit the result back to the new repository.

If the workflow does not run in your GitHub environment, run the bootstrap
script manually:

```bash
python scripts/bootstrap_template.py your-repository-name
```

The bootstrap script:

- renames the source package directory
- updates package metadata in `pyproject.toml`
- rewrites imports and tool configuration from the template package name
- updates README and documentation titles
- adjusts the supported Python versions in tox and CI when requested

Use explicit options when the defaults inferred from the repository name are not
enough:

```bash
python scripts/bootstrap_template.py your-repository-name \
  --package-name your_package \
  --project-title "Your Project" \
  --author "Your Name" \
  --author-email "you@example.com" \
  --description "Short project description." \
  --minimum-python-version 3.12
```

Repository names may contain dashes. The default Python package name is the
repository name with dashes converted to underscores.

## Install dependencies

Install the project for development:

```bash
uv sync --extra dev --extra docs
```

Install only runtime dependencies:

```bash
uv sync
```

Using pip is also supported:

```bash
pip install -e .[dev,docs]
```

## Run checks

Run tests for the active Python environment:

```bash
uv run pytest
```

Run type checks:

```bash
uv run tox -e type
```

Run coverage with the configured threshold:

```bash
uv run tox -e coverage
```

The `Coverage` workflow updates the README badge and summary from `coverage.xml` on pushes to `main` and `dev`.

Audit dependencies for known vulnerabilities:

```bash
uv run tox -e security
```

Run Ruff fixes and formatting:

```bash
uv run tox -e formatter
```

Build and smoke-test the package artifacts:

```bash
uv run tox -e build
```

Build the documentation:

```bash
uv run tox -e docs
```

Build and smoke-test the Docker image:

```bash
docker build --pull -t python-template:ci .
docker run --rm python-template:ci uv run python -c "import project_name"
```

See `CONTRIBUTING.md` for the full local verification workflow and the
generated-project smoke test.

## Commit, license, and release workflow

Three pieces of automation depend on each other, in this order: commit
messages feed the changelog, license headers are added while you commit, and
the release command turns both into a tagged GitHub Release.

### 1. Commit

Install the git hooks once per clone. Without this, the hooks only run when you
invoke them by hand:

```bash
uv run pre-commit install
```

From then on every `git commit` formats and lints the staged files, inserts
missing license headers, and verifies REUSE compliance. Run the same hooks
across the whole repository at any time:

```bash
uv run pre-commit run --all-files
```

If a hook rewrites a file, the commit is aborted with the fix already applied
to your working tree — stage it and commit again:

```bash
git add -A
git commit -m "feat(greeter): add localized greetings"
```

**Commit messages must follow the Conventional Commits format**, because
`cliff.toml` derives the changelog from the message prefix. Use
`type: subject` or `type(scope): subject`:

| Prefix                        | Changelog section |
| ----------------------------- | ----------------- |
| `feat:`                       | Features          |
| `fix:`                        | Bug Fixes         |
| `perf:`                       | Performance       |
| `refactor:`                   | Refactoring       |
| `docs:`                       | Documentation     |
| `test:`                       | Testing           |
| `build:`, `ci:`               | Build & CI        |
| `chore:`, `style:`, `format:` | Chores            |
| anything else                 | Other             |

Only the subject after the prefix reaches the changelog, so write the subject
as a standalone sentence. Merge commits and `chore(release):` commits are
skipped, which keeps release commits out of their own changelog.

### 2. License headers

Headers are appended automatically — you do not normally run anything. The
`add SPDX headers` hook calls `scripts/add_spdx_headers.py` on every staged
Python file, which shells out to `reuse annotate` and writes:

```python
# SPDX-FileCopyrightText: 2026 the Python Template contributors
#
# SPDX-License-Identifier: BSD-2-Clause
```

Existing headers are left alone, and zero-byte files (such as empty
`__init__.py`) are skipped. The `reuse lint` hook then fails the commit if any
file still lacks copyright or license information.

To annotate or check files outside a commit, drive the hooks directly:

```bash
uv run pre-commit run reuse-annotate --files project_name/greeter.py
uv run pre-commit run reuse --all-files
```

`reuse` itself is installed only inside that hook's environment, not as a
project dependency, so calling the script directly needs the tool supplied.
Do that when you need a different year or copyright holder than the defaults:

```bash
uv run --with 'reuse>=6.2,<7' python scripts/add_spdx_headers.py \
  --year 2027 --copyright "Your Name" project_name/greeter.py
```

Non-Python files are covered in bulk by `REUSE.toml` instead of an in-file
header, which is why config files, workflows, and Markdown carry no comment
block. Add new paths to the `path` list there rather than editing those files.
The license text itself lives in `LICENSES/BSD-2-Clause.txt`; REUSE requires
every identifier used anywhere in the repository to have a matching file in
that directory. When test fixtures or docs need to quote an SPDX tag as data,
wrap the region in `REUSE-IgnoreStart` / `REUSE-IgnoreEnd` comments so it is
not mistaken for a real annotation.

### 3. Release and changelog

Preview what the changelog would contain, without writing anything:

```bash
uv run tox -e changelog                     # unreleased commits
uv run tox -e changelog -- --tag v0.1.0     # as it would look tagged v0.1.0
uv run tox -e changelog -- -o CHANGELOG.md  # regenerate the file in place
```

`CHANGELOG.md` is generated, never hand-edited. Fix a wrong entry by amending
the commit message it came from and regenerating.

Then cut the release. Start with a dry run, which prints the planned steps and
touches nothing:

```bash
uv run tox -e release -- 0.1.0 --dry-run
```

When it looks right, run it for real from a clean working tree:

```bash
uv run tox -e release -- 0.1.0          # bump, changelog, commit, tag
uv run tox -e release -- 0.1.0 --push   # ...and push the branch and tag
```

The release command refuses to run if the version is not `X.Y.Z`, if the tag
already exists, or if the working tree has uncommitted changes. Otherwise it:

1. bumps `version` in `pyproject.toml`
1. runs `uv lock` and `uv lock --check`, so the lockfile matches the new
   version and CI's `--locked` installs keep working
1. writes the new section into `CHANGELOG.md` — a full render for the first
   release, prepended above the previous section afterwards
1. commits the three files as `chore(release): v0.1.0`
1. creates the annotated tag `v0.1.0`

Add `--no-tag` to produce the commit without a tag. Nothing is pushed unless
you pass `--push`; otherwise push when ready:

```bash
git push origin HEAD --follow-tags
```

Pushing a `v*` tag triggers the `Release` workflow, which verifies the tag
matches the `pyproject.toml` version, builds and smoke-tests the
distributions with `tox -e build`, extracts that version's changelog section
as the release notes, and publishes a GitHub Release with the wheel and sdist
attached. Publishing to PyPI is opt-in — see the commented `publish` job in
`.github/workflows/release.yaml` for the Trusted Publisher setup.

## Documentation

Documentation lives in `docs/` and is built with Sphinx. Manual pages are
written in Markdown with MyST, while API reference pages are generated from
Google-style Python docstrings.

The canonical documentation build is:

```bash
uv run tox -e docs
```

This runs Sphinx with warnings treated as errors and writes HTML to
`docs/_build/html`. Use a live preview while editing docs:

```bash
uv run sphinx-autobuild docs docs/_build/html
```

The live preview is for authoring convenience; `tox -e docs` is the build that
must pass before merging. Read the Docs builds the site from
`.readthedocs.yaml`, and GitHub Actions uploads the built HTML as an artifact on
pull requests.

## Project structure

| Path            | Status   | Purpose                                                                   |
| --------------- | -------- | ------------------------------------------------------------------------- |
| `.github/`      | Optional | GitHub Actions, Dependabot, and repository guidance.                      |
| `LICENSES/`     | Required | Full text of every SPDX license used, as REUSE requires.                  |
| `docs/`         | Required | Sphinx documentation, including manual pages and generated API reference. |
| `examples/`     | Optional | Runnable examples for users and contributors.                             |
| `project_name/` | Required | Source package. The bootstrap script renames this directory.              |
| `scripts/`      | Optional | Repository automation scripts, including the bootstrap script.            |
| `tests/`        | Required | Pytest test suite. Mirror the package structure where practical.          |
| `Dockerfile`    | Optional | Container build for running the project example.                          |
| `REUSE.toml`    | Optional | Bulk SPDX annotations for files that carry no in-file header.             |
| `cliff.toml`    | Optional | git-cliff changelog generation rules.                                     |
| `tox.ini`       | Required | Local and CI task definitions.                                            |

## Included tools

- [uv](https://docs.astral.sh/uv/) for dependency management
- [Tox](https://tox.wiki/en/latest/) for repeatable test and build tasks
- [Pytest](https://docs.pytest.org/en/stable/) for tests
- [Ruff](https://docs.astral.sh/ruff/) for linting and formatting
- [Pyrefly](https://pyrefly.org/) for static type checking
- [Sphinx](https://www.sphinx-doc.org/) for documentation generation
- [MyST Parser](https://myst-parser.readthedocs.io/) for Markdown in Sphinx
- [Read the Docs](https://readthedocs.org/) for hosted documentation
- [pip-audit](https://pypi.org/project/pip-audit/) for dependency vulnerability checks
- [git-cliff](https://git-cliff.org/) for changelog generation
- [REUSE](https://reuse.software/) for SPDX license headers and compliance
- [pre-commit](https://pre-commit.com/) for the commit-time hook suite
- [GitHub Actions](https://docs.github.com/en/actions) for CI automation
