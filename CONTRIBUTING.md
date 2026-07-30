# Contributing

This repository is a project template. Changes should preserve two use cases:
working on the template itself and generating a clean downstream project from
it.

## Setup

Install the development and documentation dependencies:

```bash
uv sync --extra dev --extra docs
```

Install pre-commit hooks if you want local checks before each commit:

```bash
uv run pre-commit install
```

## Local checks

Run the unit tests:

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

Preview the generated changelog:

```bash
uv run tox -e changelog
```

Prepare a release — bumps the version, regenerates the changelog, commits,
and tags:

```bash
uv run tox -e release -- 0.1.0
uv run tox -e release -- 0.1.0 --push
```

Pushing the tag triggers the `Release` workflow, which builds the
distributions and publishes a GitHub Release.

Build and smoke-test the Docker image:

```bash
docker build --pull -t python-template:ci .
docker run --rm python-template:ci uv run python -c "import project_name"
```

Build the documentation exactly as CI does:

```bash
uv run tox -e docs
```

## Documentation

Manual docs live in `docs/` and use MyST Markdown. API docs are generated from
Google-style docstrings in the source package. Keep public modules, classes,
and functions documented when adding or changing APIs.

Use a live documentation preview while editing prose or docstrings:

```bash
uv run sphinx-autobuild docs docs/_build/html
```

Before opening a pull request, run the strict build with `uv run tox -e docs`.

## Template bootstrap changes

When changing placeholder behavior, update `scripts/bootstrap_template.py` and
the bootstrap tests together. The script must keep generated repositories
usable with locked dependency installs.

Run the generated-project smoke test for changes that affect packaging,
documentation, CI, tox, or bootstrap behavior:

```bash
uv run tox -e template
```

That test creates a temporary project from the template, bootstraps it, syncs it
with `uv --locked`, imports the renamed package, runs its example tests, builds
docs, and validates distribution artifacts.

## Pull requests

A good pull request should include:

- a clear description of the template behavior being changed
- tests for bootstrap or generated-project behavior when relevant
- documentation updates for user-facing workflow changes
- passing tests, coverage, security audit, type checks, docs build, package build, and Docker build when relevant

## Release notes

`CHANGELOG.md` is generated from commit messages by git-cliff — do not edit it
by hand. What lands in it is decided by the Conventional Commits prefix on each
commit, so write commit subjects that read as release notes on their own,
especially for changes that affect generated projects, supported Python
versions, dependency management, CI behavior, documentation publishing, or the
public template workflow.

Preview the result before opening a pull request:

```bash
uv run tox -e changelog
```

The prefix-to-section mapping and the full release procedure are documented in
the "Commit, license, and release workflow" section of `README.md`.
